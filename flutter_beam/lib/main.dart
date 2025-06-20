import 'package:flutter/material.dart';
import 'dart:math' as math;

void main() {
  runApp(const BeamCalculatorApp());
}

class BeamCalculatorApp extends StatelessWidget {
  const BeamCalculatorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      home: BeamCalculatorPage(),
    );
  }
}

class BeamCalculatorPage extends StatefulWidget {
  const BeamCalculatorPage({super.key});

  @override
  State<BeamCalculatorPage> createState() => _BeamCalculatorPageState();
}

class _BeamCalculatorPageState extends State<BeamCalculatorPage> {
  final TextEditingController _lengthController = TextEditingController();
  final TextEditingController _loadController = TextEditingController();
  final TextEditingController _modulusController = TextEditingController();
  final TextEditingController _inertiaController = TextEditingController();

  double? _moment;
  double? _deflection;

  void _calculate() {
    final length = double.tryParse(_lengthController.text);
    final load = double.tryParse(_loadController.text);
    final modulus = double.tryParse(_modulusController.text);
    final inertia = double.tryParse(_inertiaController.text);

    if (length == null || load == null || modulus == null || inertia == null) {
      setState(() {
        _moment = null;
        _deflection = null;
      });
      return;
    }

    final moment = load * length / 4.0;
    final deflection = load * math.pow(length, 3) / (48.0 * modulus * inertia);

    setState(() {
      _moment = moment;
      _deflection = deflection;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Beam Calculator')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            TextField(
              controller: _lengthController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Length (m)'),
            ),
            TextField(
              controller: _loadController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Load (N)'),
            ),
            TextField(
              controller: _modulusController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Elastic modulus (Pa)'),
            ),
            TextField(
              controller: _inertiaController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(labelText: 'Moment of inertia (m^4)'),
            ),
            const SizedBox(height: 16),
            ElevatedButton(
              onPressed: _calculate,
              child: const Text('Calculate'),
            ),
            const SizedBox(height: 16),
            if (_moment != null && _deflection != null) ...[
              Text('Max bending moment: ${_moment!.toStringAsFixed(2)} Nm'),
              Text('Max deflection: ${_deflection!.toStringAsExponential(2)} m'),
            ],
          ],
        ),
      ),
    );
  }
}
