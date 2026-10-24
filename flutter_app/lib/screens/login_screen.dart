// Sign-in, registration, or guest browsing.
// Guest browsing covers the directory and lost-and-found; booking,
// pets and breed ID need a signed-in customer account.
import 'package:flutter/material.dart';
import '../state.dart';
import '../theme.dart';

class LoginScreen extends StatefulWidget {
  final AppState state;
  final VoidCallback onSignedIn;
  final VoidCallback onGuest;
  const LoginScreen({
    super.key,
    required this.state,
    required this.onSignedIn,
    required this.onGuest,
  });
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _name = TextEditingController();
  bool _register = false;
  String? _error;
  bool _busy = false;

  Future<void> _submit() async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_register) {
        await widget.state.api.registerCustomer(
            _name.text.trim(), _email.text.trim(), _password.text);
        widget.state.signedIn = true;
      } else {
        await widget.state.signIn(_email.text.trim(), _password.text);
      }
      widget.onSignedIn();
    } on Exception catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('PetBridge',
                    style: TextStyle(
                        fontSize: 34,
                        fontWeight: FontWeight.w900,
                        color: PbColors.deepTeal)),
                const Text(
                    'A notebook for your pets, their doctors, and their people.',
                    style: TextStyle(fontSize: 16, color: PbColors.ink)),
                const SizedBox(height: 28),
                if (_register)
                  TextField(
                      controller: _name,
                      decoration:
                          const InputDecoration(labelText: 'Full name')),
                if (_register) const SizedBox(height: 12),
                TextField(
                    controller: _email,
                    decoration: const InputDecoration(labelText: 'Email')),
                const SizedBox(height: 12),
                TextField(
                    controller: _password,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: 'Password')),
                if (_error != null) ...[
                  const SizedBox(height: 12),
                  Text(_error!, style: const TextStyle(color: PbColors.brick)),
                ],
                const SizedBox(height: 20),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _busy ? null : _submit,
                    child: Text(_register ? 'Create account' : 'Sign in'),
                  ),
                ),
                TextButton(
                  onPressed: () => setState(() => _register = !_register),
                  child: Text(_register
                      ? 'Already have an account? Sign in'
                      : 'New here? Create a customer account'),
                ),
                const Divider(),
                TextButton(
                  onPressed: widget.onGuest,
                  child: const Text(
                      'Browse services and lost pets without signing in'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
