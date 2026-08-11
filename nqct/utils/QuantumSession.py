from __future__ import annotations

from pathlib import Path

from nqct.client import NQCTClient
from nqct.models.backend import Backend
from nqct.models.execution import normalize_acquisition_type, normalize_averaging
from IPython.display import display
from sqdtoolz.Utilities.OpenQASM.ParserOpenQASM import ParserOpenQASM
import pandas as pd
from sqdtoolz.Utilities.OpenQASM.ScheduleParametersJSONConfigZI import ScheduleParametersJSONConfigZI
from sqdtoolz.Utilities.FileJSON import SerialiseJSON
from nqct.models.execution import QubitMappingEntry
import shutil

class QuantumSession:
    def __init__(self, api_key:str=None, storage_path = 'temp/'):
        """
        If api_key is None, it will resort to the saved key on the system...
        """
        self._client = NQCTClient(api_key=api_key)
        self._sel_backend = None
        self._qasm = ""
        self._num_shots = 1024
        self._qreg_phys_mapping = {}
        self._numpy_arrays = {}
        self._acquisition_type = 'Discrimination'
        self._averaging = 'AverageRepetitions'
        self._shot_repeat = 1
        self._storage_path = storage_path
    
    def list_backends(self, print_table=True) -> list[Backend]:
        leBackends = self._client.backends(status="online")
        if print_table:
            data = {
                'Name': [x.name for x in leBackends],
                'Backend ID': [x.id for x in leBackends],
                'Qubits': [x.qubits for x in leBackends],
            }
            display(pd.DataFrame(data))
        return leBackends

    def select_backend(self, leBackend:Backend|str):
        if isinstance(leBackend, Backend):
            self._sel_backend = leBackend
        else:
            leBackends = self.list_backends(False)
            found = False
            for cur_backend in leBackends:
                if cur_backend.id == leBackend:
                    found = True
                    break
            assert found, f"Cannot find backend with ID: {leBackend}"
            self._sel_backend = cur_backend
    
    def set_qasm(self, qasm_script:str):
        self._qasm = qasm_script
    
    def load_qasm(self, file_path:str):
        with open(file_path, 'r') as f:
            qasm_script = f.read()
        self._qasm = qasm_script

    def set_num_shots(self, num_shots:int):
        self._num_shots = num_shots

    def set_acquisition_type(self, acq_type: str) -> None:
        """Set hardware acquisition_type (Discrimination | Integration | Raw)."""
        self._acquisition_type = normalize_acquisition_type(acq_type)

    def set_averaging_type(self, averaging: str) -> None:
        """Set hardware averaging (AverageRepetitions | SingleShotCounts)."""
        self._averaging = normalize_averaging(averaging)

    def set_shot_repeat(self, shot_repeat: int) -> None:
        """Set the number of software repeats for hardware execution."""
        if not isinstance(shot_repeat, int) or isinstance(shot_repeat, bool) or shot_repeat < 1:
            raise ValueError(
                f"shot_repeat must be an integer >= 1, got {shot_repeat!r}"
            )
        self._shot_repeat = shot_repeat

    def get_qregs_in_qasm(self):
        poqasm = ParserOpenQASM('', [], main_qasm=self.get_final_qasm())
        return poqasm.get_qregs()
    
    def set_qreg_physical_mapping(self, mapping:dict):
        """
        A dictionary that maps the qreg to the physical qubit index. For example, q[0] mapped onto $1 becomes the key-value pair (q,0):1.
        An empty dictionary implies that it is the default mapping (order of qregs defined map onto the physical qubits directly)
        """
        self._qreg_phys_mapping = mapping

    def declare_numpy_waveform(self, wfm_name, numpy_array):
        self._numpy_arrays[wfm_name] = numpy_array
    def clear_numpy_waveforms(self):
        self._numpy_arrays = {}

    def validate(self, print_output=True):
        if self._sel_backend.type == 'hardware':
            poqasm = ParserOpenQASM('', [], measure_label='QMEAS', main_qasm=self.get_final_qasm())
            if len(self._qreg_phys_mapping) > 0:
                poqasm.set_qreg_physical_mapping(self._qreg_phys_mapping)
            poqasm.perform_parsing()
            #TODO: Run key-checking asserts...
            leScheduleParams = ScheduleParametersJSONConfigZI(self._sel_backend.backend_metadata['topology']['calibration']['payload'])
            leSchedule = poqasm.create_schedule(leScheduleParams, flatten_blocks=True)
            leScheduleTable = poqasm.tabulate_schedule(leSchedule, leScheduleParams)
            if print_output:
                display(leScheduleTable)
            #
            poqasm.check_ZI_compatibility(leSchedule, leScheduleParams)
            max_shots = poqasm.check_ZI_max_shots(leSchedule, leScheduleParams, self._acquisition_type, self._averaging)
            assert max_shots >= self._num_shots, (
                f"To fit this measurement in memory, only {max_shots} shots can be "
                "taken in real time; reduce shots or use set_shot_repeat() for "
                "additional software repeats."
            )
        else:
            #Perhaps just check qubit counts?
            pass

    def get_final_qasm(self):
        decls = ";\n\ncal {\n"
        for cur_array in self._numpy_arrays:
            cur_encoded = SerialiseJSON.encode_ndarray(self._numpy_arrays[cur_array], True)
            decls += f"\twaveform {cur_array} = load_numpy_encoded(0x{cur_encoded});\n"
        decls += "}\n\n"
        return self._qasm.replace(";", decls, 1)

    def run(self, auto_validate=True, dont_download_raw=False):
        if auto_validate:
            self.validate(False)
        job = self._client.submit_job(
            qasm=self._qasm,
            backend_id=self._sel_backend.id,
            shots=self._num_shots,
            source="api",
            acquisition_type=self._acquisition_type,
            averaging=self._averaging,
            shot_repeat=self._shot_repeat,
            qubit_mapping=[QubitMappingEntry(qreg=x[0], qreg_index=x[1], phyq_index=self._qreg_phys_mapping[x]) for x in self._qreg_phys_mapping]
        )
        job = job.wait(timeout=3600)
        ret_val = job.result()
        #
        if not dont_download_raw:
            uid = str(job.id)
            temp_zip_path = self._storage_path + 'temp.zip'
            self.download_bundle(uid, temp_zip_path)
            shutil.unpack_archive(temp_zip_path, self._storage_path + uid + '/')
        #
        return ret_val

    def download_bundle(self, job_id: str, path: str | Path | None = None) -> Path:
        """``GET /jobs/{id}/artifacts/bundle`` — download hardware result zip.

        Fetches the job then calls ``Job.download_bundle``.
        """
        job = self._client.job(job_id)
        return job.download_bundle(path)

    def close(self):
        self._client.close()
    def reconnect(self, api_key=""):
        """
        If api_key is blank, it will resort to the saved key on the system...
        """
        self._client = NQCTClient(api_key=api_key)

