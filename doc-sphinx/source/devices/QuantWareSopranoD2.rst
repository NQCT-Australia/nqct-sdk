.. _devices-quantware-d2:

QuantWare Soprano D2
====================

This is a 5-Qubit superconducting transmon device connected in a star topology:


.. figure:: /_static/DevicesQuantWareD2.drawio.svg
   :align: center
   :alt: Device topology of 5-Qubit QuantWare Soprano D2

   Device topology of 5-Qubit QuantWare Soprano D2

The five flux-tunable transmon qubits are labelled Q0, Q1, Q2, Q3 and Q4. The vertices linking Q2 to the other qubits represent fixed two-qubit resonator couplers.


Single Qubit Hamiltonian
------------------------

The individual transmon qubits have:

- A charge line for :math:`\sigma_x` and :math:`\sigma_y` control (i.e. qubit rotations about :math:`x` and :math:`y` axes)
- A flux line for :math:`\sigma_z` control (i.e. energy splitting)
- A readout resonator (note that all readout resonators are interfaced via a shared multiplexed signal line)

The qubits follow the standard Hamiltonian (under truncation of the Taylor series for cosine arising from the Josephson junction's nonlinearity):

.. math::
    \begin{aligned}\mathcal{H}\approx&\hbar\omega_q(a^\dagger_qa_q+\tfrac{1}{2})+\frac{\hbar\alpha}{2}a_q^\dagger a_q^\dagger a_qa_q \\&+ \hbar\omega_c(a^\dagger_ca_c+\tfrac{1}{2}) - \hbar g_c(a_q-a_q^\dagger)(a_c-a_c^\dagger)\ \\&+ \hbar\omega_r(a^\dagger_ra_r+\tfrac{1}{2}) - \hbar g_r(a_q-a_q^\dagger)(a_r-a_r^\dagger)\end{aligned}

where the first line describes the individual qubit :math:`q`, the second line describes the coupling of the qubit to its charge line, while the third line describes the coupling of the qubit to its readout resonator. The qubit angular frequency :math:`\omega_q` is tunable via its flux line up to its maximum frequency :math:`\omega_q^\max`. The qubit anharmonicity (the perturbation lowers the energy separation between the first and second excited states) :math:`\alpha` also changes from its maxumum :math:`\alpha^\max` when tuning the flux line. The charge line operates around the qubit frequency, whereas the resonator operates in the dispersive limit and does not change the qubit population. The effective two-level system comprised of the qubit and its charge-line is (under the rotating wave approximation):

.. math::
    \mathcal{H}_\text{eff}=\hbar\frac{\omega_q-\omega}{2}\sigma_z + E_{ac}(\cos(\varphi)\sigma_x+\sin(\varphi)\sigma_y)

where :math:`\omega` and :math:`\varphi` represent the drive frequency and phase of the RF signal applied on the charge line. The amplitude of the charge-line RF signal is :math:`E_{ac}=\hbar g_c\sqrt{N+1}` (with :math:`N` being the number of photons in the charge line). Notice that when the RF frequency in the drive line is on resonance with the qubit, the rotations are purely about an axis (with polar angle $\varphi$) on the :math:`xy` plane.

For readout, the resonator frequency shifts by :math:`2\chi` when the qubit is in the excited state (relative to when it is in the ground state) with:

.. math::
    \chi=-\frac{\alpha g_r^2}{\Delta(\Delta-\alpha)}-\frac{\alpha g_r^2}{\Sigma(\Sigma-\alpha)}

where :math:`\Delta=\omega_q-\omega_r` and :math:`\Sigma=\omega_q+\omega_r`.

The following table lists the typical fixed device parameters.


.. list-table:: Qubit Hamiltonian parameters
   :align: center
   :header-rows: 1

   * - Qubit
     - :math:`\omega_q` (GHz)
     - :math:`\alpha` (MHz)
     - :math:`\omega_r` (GHz)
     - :math:`\chi` (kHz)
   * - Q0
     - 5.141
     - -214.4
     - 7.263
     - -363.3
   * - Q1
     - 5.119
     - -216.0
     - 7.412
     - -375.0
   * - Q2
     - 5.882
     - -204.9
     - 7.548
     - -405.8
   * - Q3
     - 5.762
     - -190.3
     - 7.707
     - -589.0
   * - Q4
     - 5.720
     - -194.2
     - 7.858
     - -374.0


For the latest set of device parameters, refer to the NQCT cloud dashboard.


Two-Qubit Hamiltonian
---------------------

The qubits are linked via fixed resonator couplers. The effective coupling Hamiltonian over the first three energy levels is:

.. math::
    \mathcal{H}_\text{cpl}=\hbar J(\lvert01\rangle\langle10\lvert+\lvert10\rangle\langle01\lvert) + \hbar\zeta_{02}(\lvert02\rangle\langle11\lvert+\lvert11\rangle\langle02\lvert) + \hbar\zeta_{20}(\lvert20\rangle\langle11\lvert+\lvert11\rangle\langle20\lvert)

where the three anti-crossings appear at:

- :math:`J`: :math:`\omega_1\approx\omega_2`
- :math:`\zeta_{02}`: :math:`\omega_1\approx\omega_2-\alpha_2`
- :math:`\zeta_{20}`: :math:`\omega_2\approx\omega_1+\alpha_1`

with :math:`\omega_i` being the qubit frequency and :math:`\alpha_i` the anharmonicity of the respective qubits. A typical controlled-phase (e.g. CZ) operation involves tuning to the :math:`\zeta_{20}` anti-crossing to perturb the :math:`\lvert11\rangle` state. Note that when including the individual qubit Hamiltonians, a large energy difference between the qubits will disable the two-qubit gate

The typical two-qubit parameters are:

.. list-table:: Coupling Hamiltonian parameters
   :align: center
   :header-rows: 1

   * - Coupling
     - :math:`J` (MHz)
     - :math:`\zeta_{02}` (MHz)
     - :math:`\zeta_{20}` (MHz)
   * - Q0/Q1
     - 0
     - 0
     - 0

For the latest set of device parameters, refer to the NQCT cloud dashboard.
