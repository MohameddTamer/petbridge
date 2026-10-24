// PetBridge client app: sign in, then the customer notebook.
// Guest browsing opens the directory without a session.
import 'package:flutter/material.dart';
import 'api.dart';
import 'models.dart';
import 'screens/booking_screen.dart';
import 'screens/breed_screen.dart';
import 'screens/home_screen.dart';
import 'screens/login_screen.dart';
import 'screens/lost_found_screen.dart';
import 'screens/pet_screen.dart';
import 'screens/services_screen.dart';
import 'state.dart';
import 'theme.dart';

void main() {
  // One configurable base URL, overridable at build time:
  // flutter run --dart-define=PETBRIDGE_BASE_URL=http://host:8765
  const baseUrl = String.fromEnvironment(
    'PETBRIDGE_BASE_URL',
    defaultValue: defaultBaseUrl,
  );
  runApp(PetBridgeApp(api: ApiClient(baseUrl: baseUrl)));
}

enum _Page { login, home, services, booking, pet, lostFound, breed }

class PetBridgeApp extends StatefulWidget {
  final ApiClient api;
  const PetBridgeApp({super.key, required this.api});
  @override
  State<PetBridgeApp> createState() => _PetBridgeAppState();
}

class _PetBridgeAppState extends State<PetBridgeApp> {
  late final AppState _state;
  _Page _page = _Page.login;
  Pet? _pet;
  ProviderEntry? _provider;
  DirectoryService? _service;

  @override
  void initState() {
    super.initState();
    _state = AppState(api: widget.api);
  }

  void _go(_Page page) => setState(() => _page = page);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PetBridge',
      theme: pbTheme(),
      home: switch (_page) {
        _Page.login => LoginScreen(
            state: _state,
            onSignedIn: () => _go(_Page.home),
            onGuest: () => _go(_Page.services),
          ),
        _Page.home => HomeScreen(
            state: _state,
            onPet: (pet) {
              _pet = pet;
              _go(_Page.pet);
            },
            onServices: () => _go(_Page.services),
            onLostFound: () => _go(_Page.lostFound),
            onBreed: () => _go(_Page.breed),
            onSignOut: () => _go(_Page.login),
          ),
        _Page.services => ServicesScreen(
            api: widget.api,
            onBook: (provider, service) {
              if (!_state.signedIn) {
                _go(_Page.login);
                return;
              }
              _provider = provider;
              _service = service;
              _go(_Page.booking);
            },
          ),
        _Page.booking => BookingScreen(
            state: _state,
            provider: _provider!,
            service: _service!,
          ),
        _Page.pet => PetScreen(api: widget.api, pet: _pet!),
        _Page.lostFound => LostFoundScreen(api: widget.api),
        _Page.breed => BreedScreen(api: widget.api),
      },
    );
  }
}
