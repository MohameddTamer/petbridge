// The Hand-Drawn Companion palette and shapes.
// Warm paper, ink, crayon teal and ochre only. No gradients, no shadows
// pretending to be depth, no purple anywhere.
import 'package:flutter/material.dart';

class PbColors {
  static const paper = Color(0xFFFFFDF8);
  static const ink = Color(0xFF22301F);
  static const teal = Color(0xFF2E7D6B);
  static const deepTeal = Color(0xFF0E4F45);
  static const ochre = Color(0xFFE3A72F);
  static const brick = Color(0xFFB3402A);
  static const softTeal = Color(0xFFE4EFEB);
  static const softOchre = Color(0xFFFBF0D3);
}

ThemeData pbTheme() {
  return ThemeData(
    scaffoldBackgroundColor: PbColors.paper,
    colorScheme: const ColorScheme.light(
      primary: PbColors.deepTeal,
      secondary: PbColors.teal,
      surface: PbColors.paper,
      error: PbColors.brick,
    ),
    textTheme: const TextTheme(
      displaySmall: TextStyle(
          fontSize: 26, fontWeight: FontWeight.w800, color: PbColors.ink),
      titleLarge: TextStyle(
          fontSize: 20, fontWeight: FontWeight.w800, color: PbColors.ink),
      titleMedium: TextStyle(
          fontSize: 16, fontWeight: FontWeight.w700, color: PbColors.ink),
      bodyMedium: TextStyle(fontSize: 15, color: PbColors.ink),
      bodySmall: TextStyle(fontSize: 13, color: PbColors.ink),
      labelLarge: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
    ),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(
        backgroundColor: PbColors.deepTeal,
        foregroundColor: Colors.white,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(14),
        ),
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 14),
      ),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: PbColors.ink, width: 1.2),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: PbColors.ink, width: 1.2),
      ),
    ),
    fontFamilyFallback: const ['Nunito', 'Segoe UI', 'Tahoma'],
  );
}

// A hand-cut corner shape: slightly uneven radii, drawn not machined.
BorderRadius handCutRadius() => const BorderRadius.only(
      topLeft: Radius.elliptical(22, 14),
      topRight: Radius.elliptical(14, 22),
      bottomLeft: Radius.elliptical(16, 20),
      bottomRight: Radius.elliptical(20, 14),
    );
