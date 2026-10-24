// Small hand-drawn pieces: tape strips, dashed stitch lines, paw prints
// and a 2px-stroke icon family. Everything is painted, nothing is emoji.
import 'package:flutter/material.dart';
import '../theme.dart';

class WashiTape extends StatelessWidget {
  final Color color;
  const WashiTape({super.key, required this.color});
  @override
  Widget build(BuildContext context) {
    return Transform.rotate(
      angle: -0.05,
      child: Container(
        width: 96,
        height: 24,
        decoration: BoxDecoration(
          color: color.withValues(alpha: 0.55),
          border: Border.all(color: color.withValues(alpha: 0.4)),
        ),
      ),
    );
  }
}

class StitchLine extends StatelessWidget {
  final double height;
  final Color color;
  const StitchLine({super.key, this.height = 120, required this.color});
  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      size: Size(2, height),
      painter: _DashPainter(color),
    );
  }
}

class _DashPainter extends CustomPainter {
  final Color color;
  _DashPainter(this.color);
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = color
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;
    var y = 0.0;
    while (y < size.height) {
      canvas.drawLine(Offset(0, y), Offset(0, y + 8), paint);
      y += 14;
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}

class PawTrail extends StatelessWidget {
  const PawTrail({super.key});
  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        for (var i = 0; i < 6; i++) ...[
          Icon(Icons.pets,
              size: 18, color: PbColors.teal.withValues(alpha: 0.45)),
          const SizedBox(width: 14),
        ],
      ],
    );
  }
}

// One drawn icon family: simple 2px-style glyphs from the material set,
// used in teal or ink only, never as decoration on numbers.
class DrawnIcon extends StatelessWidget {
  final IconData icon;
  final double size;
  final Color color;
  const DrawnIcon(this.icon,
      {super.key, this.size = 22, this.color = PbColors.teal});
  @override
  Widget build(BuildContext context) =>
      Icon(icon, size: size, color: color);
}

// The booking confirmation flourish: a hand-drawn ellipse around text.
class CircledText extends StatelessWidget {
  final String text;
  const CircledText(this.text, {super.key});
  @override
  Widget build(BuildContext context) {
    return CustomPaint(
      painter: _EllipsePainter(),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 12),
        child: Text(text,
            style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w800,
                color: PbColors.deepTeal)),
      ),
    );
  }
}

class _EllipsePainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = PbColors.ochre
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round;
    final rect = Rect.fromLTWH(2, 2, size.width - 4, size.height - 4);
    canvas.drawOval(rect, paint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter old) => false;
}
