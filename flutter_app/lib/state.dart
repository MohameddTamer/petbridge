// One small holder for session and home data.
// Screens read from here so they never fetch behind each other's backs.
import 'package:flutter/foundation.dart';
import 'api.dart';
import 'models.dart';

class AppState extends ChangeNotifier {
  final ApiClient api;
  bool signedIn = false;
  bool tourDone = false;
  List<Pet> pets = [];
  List<Map<String, dynamic>> due = [];
  List<Booking> bookings = [];
  String? homeError;

  AppState({ApiClient? api}) : api = api ?? ApiClient();

  Future<void> signIn(String email, String password) async {
    await api.login(email, password);
    signedIn = true;
    notifyListeners();
  }

  Future<void> refreshHome() async {
    try {
      final data = await api.home();
      pets = data.pets;
      due = data.due;
      bookings = data.bookings;
      homeError = null;
    } on ApiException catch (e) {
      homeError = e.message;
    } catch (_) {
      // Any other network surprise becomes a banner, never a crash,
      // and the pets already on screen stay put.
      homeError = 'Could not load home data.';
    }
    notifyListeners();
  }

  void signOut() {
    api.token = null;
    signedIn = false;
    pets = [];
    due = [];
    bookings = [];
    notifyListeners();
  }
}
