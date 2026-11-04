.. _oqasmpulsecompilersupport:

Supported Features & Rules
==========================

NQCT follows the `OpenQASM3 standard <https://openqasm.com/versions/3.0/intro.html>`__. Support for the full standard is on-going. This page highlights the currently supported commands and the specific parsing behaviors of the NQCT parser. Thus, it is not a definitive resource on OpenQASM3/OpenPulse. Please refer to the full standard or the worked examples for such details.


Variable Scoping and Declarations
---------------------------------

The parser uses a state machine to manage variable scope. Variables declared within a specific scope (like a loop or a function) are not visible outside of it. There is a difference in scoping:

*   **Global Scope:** Only the following declarations are permitted in the global scope: ``gate``, ``def``, ``defcal``, ``defcalgrammar``, ``extern``, ``include``, and ``qubit``.
*   **Local Scope:** Variables declared within ``gatedef`` or ``defcal`` blocks are strictly local.
*   **Qubits:** Qubit declarations must occur in the global scope.

.. list-table:: OpenQASM Scopes
   :widths: 25 75
   :header-rows: 1

   * - Scope Type
     - Included Structures
   * - **Global**
     - ``block``, ``for``, ``if``, ``def``, ``gate``
   * - **Calibration**
     - ``cal block``, ``defcal``

.. note::
   In the script, ``gatedef`` is an OpenQASM construct and only refers to **logical** qubit registers defined via ``qubit``. Whereas, ``defcal`` is an OpenPulse construct that refers to **physical** qubits (i.e. ``$0``, ``$1``...). The name resolution on a qubit operation forces ``defcal`` to take precedence over ``gatedef``. For example, when calling a qubit operation ``x q[1]`` with ``q[1]`` mapped to ``$2``, the parser first checks if there is a ``defcal`` called ``x`` operating on ``$2``. If it is defined, then it calls the ``defcal``, otherwise it searches for a ``gatedef`` defined on a general qubit register. Thus, if one were to override ``x`` for all qubits, there must be an individual ``defcal`` for every physical qubit.


Loops
-----

The implementation of ``for`` loops is designed to align with the hardware restrictions of *LabOneQ*.

*   **Sequential Execution:** All ``for`` loops are executed sequentially. NQCT does not support parallel ``for`` loops.
*   **Nesting Constraints:** A loop can contain a single child loop. However, a loop cannot contain two parallel child loops.
*   **Dynamic Delays:** To implement dynamic delays or scaling within a loop, you must create an arithmetic offset/scaling variable alongside your main loop variable and sweep them simultaneously.

.. warning::
   **Supported loops:** To ensure strict timing adherence, ``for`` loops are unrolled during compilation. Consequently, ``while`` loops, which have termination conditions unknown at compile-time, are not supported.


Conditional statements
----------------------

Conditional statements like ``if``-statements for dynamic feedback will be supported soon.


Pulse-level Control (OpenPulse)
-------------------------------

NQCT allows for heavy use of OpenPulse-style control by leveraging the ``extern`` command. This allows you to access pulse frames without the boilerplate of defining ports and frames manually.

**Implicit Frames**
The following three ``extern`` commands are added to the parser implicitly for every qubit:

.. code-string:: qasm

   extern drive(qubit) -> frame;
   extern flux(qubit) -> frame;
   extern meas(qubit) -> frame;

That is, for any qubit, one may query the drive, flux or measure lines by using these three functions (using `meas` here as `measure` is an *OpenQASM* construct). After that, the `play` functions can be used in a straightforward manner. Note that `play` functions in `cal` blocks are ignored. To cater for the literal-only requirement in delay instructions, the same frames are by default declared as frame objects for every physical qubit (they can technically be overwritten):

.. code-string:: qasm
   drive0 = drive($0)
   flux0 = flux($0)
   meas0 = meas($0)
   //
   drive1 = drive($1)
   flux1 = flux($1)
   meas1 = meas($1)
   //
   //etc.

.. warning::
   **Supported loops:** When using ``delay`` in a ``defcal`` block, the frames must be literals due to the current state of the OpenQASM3 standard. Thus, for example, use ``delay[0] drive0, flux0;`` as opposed to ``delay[0] drive($0), flux($0)`` as the latter will throw a compilation error.

The following waveforms are available for use within the parser:

.. list-table::
   :widths: 30 70
   :header-rows: 1

   * - Waveform
     - Signature
   * - ``gaussian``
     - ``gaussian(duration, amp, sigma)``
   * - ``drag``
     - ``drag(duration, amp, sigma, beta)``
   * - ``constant``
     - ``constant(duration, amp)``

.. warning::
   **Play Function Limitations:** While you can use ``play`` functions in ``defcal`` blocks, they are **not supported** within standard ``cal`` blocks. Additionally, all ``play`` functions within a single ``defcal`` block are assumed to start from the same time point. That is, there is an implicit synchronisation of all signals within the physical qubits defined for the ``defcal`` block.
