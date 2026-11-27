.. _fluxtuning:

Flux Tuning
===========

The flux-tunable transmon qubits replace a normal singular Josephson junction with two parallel Josephson junctions to form a SQUID (superconducting quantum interference device) loop. When passing a magnetic field through this SQUID loop, the energy of the transmon can be tuned. This article highlights the basic theory on how a voltage pulse sent to the device under test maps onto a magnetic field which maps onto the subsequent qubit energy.

Basics
------

It can be shown that the maximum potential energy obtained by connecting 2 identical Josephson junctions in parallel is:

.. math::
   E_\text{SQUID} = 2E_J\left| \cos\left(\frac{e\Phi_e}{\hbar}\right)\right|

where :math:`E_J` is the Josephson energy of one of the individual Josephson junctions, :math:`\Phi_e` is the externally applied flux penetrating the SQUID loop, :math:`e` is elementary charge and :math:`\hbar` is Planck's constant over :math:`2\pi`. When setting :math:`\Phi_e=0` (or any multiple of the flux quantum), then the qubit energy is at its so-called 'sweet-spot' maximum value. In this region, the derivative :math:`\partial E_\text{qubit}/\partial\Phi_e` is zero. The SQUID oscillations have a period of the flux quantum :math:`\Phi_0=h/(2e)` in :math:`\Phi_e`.

Thus, at the sweet-spot, the qubit is least susceptible to decoherence due to flux noise. Typical operation involves the qubit tuned to the flux sweet-spot at all times with transient flux pulses used to offset the qubit energy to have it resonantly interact with other qubits when executing two-qubit gates.


Mapping voltage to flux
-----------------------

The journey of a voltage sent to the signal line connecting to the flux line of the qubit chip involves:

- Several attenuators that lower the voltage amplitude (placed to thermalise signal lines to the local fridge temperatures to thereby, lower the Johnson noise profile)
- Low-pass filters to attenuate high-frequency Johnson noise
- A 50Ω output load that connects to a superconducting flux line that is shorted to ground

That is, given the final voltage amplitude of the flux signal, the 50Ω output load limits the resulting current. Now if one calculates the flux in the SQUID loop due to a unit of current in the flux line, one has the mapping of voltage amplitude to flux amplitude. In the *NQCT API*, one may query the hardware mapping via:

.. code:: python

    dict_qubit_params = qs.get_qubit_params('Q0')   #qs is a QuantumSession object
    dict_flux_params = dict_qubit_params['FluxConversionParams']
    #
    max_qubit_freq = dict_qubit_params['DriveGE']
    volt_to_flux_conv = dict_flux_params['period']

That is, the `'FluxConversionParams'` parameter has a key `'period'` that is the voltage applied (at the input of the fridge signal line - i.e. before the attenuators and filters etc.) to inject one flux quantum :math:`\Phi_0=h/(2e)` through the SQUID loop.


Mapping flux to qubit frequency
-------------------------------

Given `'max_qubit_freq'` and `'volt_to_flux_conv'` from the previous code snippet alongside the equation for SQUID oscillations, one may obtain the qubit frequency via:

.. math::

    E_\text{qubit} = \sqrt{8E_CE_\text{SQUID}}-E_C

where :math:`E_C` is the charging energy of the transmon qubit. Note that the this equation only works in the transmon regime where :math:`E_\text{SQUID}/E_C\gg1`. For convenience, the *NQCT API* provides a convenient conversion function that maps voltage amplitude to qubit frequency:

.. code:: python

    qs.get_qubit_freq_from_amplitude('Q0', 0.47)   #qs is a QuantumSession object

where the second parameter is the flux amplitude in [-1,1].
