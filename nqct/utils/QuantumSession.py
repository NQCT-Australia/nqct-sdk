from __future__ import annotations

from nqct.client import NQCTClient
from nqct.models.backend import Backend
from nqct.models.execution import normalize_acquisition_type, normalize_averaging
from IPython.display import display
from sqdtoolz.Utilities.OpenQASM.ParserOpenQASM import ParserOpenQASM
import pandas as pd
from sqdtoolz.Utilities.OpenQASM.ScheduleParametersJSONConfigZI import ScheduleParametersJSONConfigZI

class QuantumSession:
    def __init__(self, api_key:str=None):
        """
        If api_key is None, it will resort to the saved key on the system...
        """
        self._client = NQCTClient(api_key=api_key)
        self._sel_backend = None
        self._qasm = ""
        self._num_shots = 1024
        self._qreg_phys_mapping = {}
        self._acquisition_type: str | None = None
        self._averaging: str | None = None
    
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

    def get_qregs_in_qasm(self):
        qasm_file_path = None##################NEED TO EITHER LOAD FROM TEMPORARY FILE OR INITIALISE VIA STRING
        poqasm = ParserOpenQASM(qasm_file_path, kwargs.pop('source_dirs', []), measure_label='QMEAS')
        return poqasm.get_qregs()
    
    def set_qreg_physical_mapping(self, mapping:dict):
        """
        A dictionary that maps the qreg to the physical qubit index. For example, q[0] mapped onto $1 becomes the key-value pair (q,0):1.
        An empty dictionary implies that it is the default mapping (order of qregs defined map onto the physical qubits directly)
        """
        self._qreg_phys_mapping = mapping

    def validate(self, print_output=True):
        if self._sel_backend.type == 'hardware':
            #TODO: Run key-checking asserts...
            qasm_file_path = None##################NEED TO EITHER LOAD FROM TEMPORARY FILE OR INITIALISE VIA STRING
            poqasm = ParserOpenQASM(qasm_file_path, kwargs.pop('source_dirs', []), measure_label='QMEAS')
            if len(self._qreg_phys_mapping) > 0:
                poqasm.set_qreg_physical_mapping(self._qreg_phys_mapping)
            leScheduleParams = ScheduleParametersJSONConfigZI(self._sel_backend.backend_metadata['topology']['calibration']['payload'])
            leSchedule = oqasm.create_schedule(leScheduleParams, flatten_blocks=True)
            leScheduleTable = oqasm.tabulate_schedule(leSchedule, leScheduleParams)
            if print_output:
                display(leScheduleTable)
        else:
            #Perhaps just check qubit counts?
            pass

    def run(self, auto_validate=True):
        if auto_validate:
            self.validate(False)
        job = self._client.submit_job(
            qasm=self._qasm,
            backend_id=self._sel_backend.id,
            shots=self._num_shots,
            source="api",
            acquisition_type=self._acquisition_type,
            averaging=self._averaging,
        )
        job.wait(timeout=3600)
        return job.result()


    def close(self):
        self._client.close()
    def reconnect(self, api_key=""):
        """
        If api_key is blank, it will resort to the saved key on the system...
        """
        self._client = NQCTClient(api_key=api_key)

