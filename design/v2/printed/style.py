"""Design language for v2. Every printed part imports these; no local radii.

Soft desktop-instrument look (Dobot-class arm): ivory structure, orange moving drive parts,
one M3/M4 hex drive, links tapered toward the tool.
"""
EDGE = "soft"          # fillets on visible vertical edges, 45 deg chamfer on bed edges
WALL = 2.4             # 6 perimeters of a 0.4 mm nozzle
R_OUTER = 6.0          # main corner radius of plates (towers, base, deck)
R_LINK = 4.0           # link outline corners
R_EDGE = 1.0           # touched edges
C_BED = 0.4            # bed-edge chamfer against elephant's foot
REVEAL = 0.8
GRID = 0.5
DRIVE = "M3/M4 hex socket"

COLORS = {
    "structure": "#E8E4DA",   # Ivory White PLA: base, turret, shanks, pleuel
    "accent": "#F26B21",      # Mandarin Orange PLA: pulleys, gripper fingers
    "board": "#1E5B3A",
    "metal": "#8C9096",
    "fastener": "#B8BCC2",
    "servo": "#222222",
    "belt": "#2A2A2A",
    "keepout": "#ff00ff",
}
