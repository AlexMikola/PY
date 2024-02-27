class Multi_Polygon:
    def __init__(self):
        self.polygons = []


class Polygon:
    def __init__(self):
        self.num_loops = 0


class Token:
    def __init__(self, ch, line, column):
        self.ch = ch
        self.line = line
        self.column = column


class Parser:
    def __init__(self, text):
        self.tokens = []
        line = 1
        column = 0
        for ch in text:
            column += 1
            if ch in {'(', ')', ','}:
                self.tokens.append(Token(ch, line, column))
            elif ch == '\n':
                line += 1
                column = 1
        self.multi_polygons = []
        self.token_index = 0
        self.multi = None
        self.polygon = None
        self.parse()

    def eat(self, ch):
        token = self.tokens[self.token_index]
        if ch != token.ch:
            message = "line %d, column %d, expected '%s', but found '%s'" % (token.line, token.column, ch, token.ch)
            raise Exception(message)
        self.token_index += 1

    def left_paren(self):
        self.eat('(')

    def right_paren(self):
        self.eat(')')

    def ate_comma(self):
        ch = self.tokens[self.token_index].ch
        if (ch != ','):
            return False
        self.token_index += 1
        return True

    def parse(self):
        while self.token_index < len(self.tokens):
            self.parse_multi_polygon()

    def parse_multi_polygon(self):
        self.multi = Multi_Polygon()
        self.left_paren()
        while True:
            self.parse_polygon()
            if not self.ate_comma():
                break
        self.right_paren()
        self.multi_polygons.append(self.multi)
        self.multi = None

    def parse_polygon(self):
        self.polygon = Polygon()
        self.left_paren()
        while True:
            self.parse_loop()
            if not self.ate_comma():
                break
        self.right_paren()
        self.multi.polygons.append(self.polygon)
        self.polygon = None

    def parse_loop(self):
        self.left_paren()
        num_points = 0
        while self.ate_comma():
            num_points += 1
        self.right_paren()
        self.polygon.num_loops += 1


if __name__ == '__main__':
    # txt_wkt = r"MULTIPOLYGON(((-8 0, 10 -7, 15 0, 0 14, -11 -13, -15 -5),(-6 -19, -18 -8, -9 -18, -1 2, 10 -8, -1 -12, -9 -16)),((0 19, -8 -10, -12 -12, 15 -20, 9 9, 16 5),(8 4, 8 0, 2 7, -17 8, 13 17, -6 -7)),((-9 -1, 19 9, -15 -11, -4 -14, -3 18),(-4 -15, 7 8, 5 -6, 20 13, 0 7, -10 -18)),((19 0, -13 1, -10 -12, -8 7, -1 14, 17 11),(0 -10, -1 -20, -14 7)),((-20 -7, 3 -7, 15 2, -7 -7),(9 -18, 13 -2, -15 -8, -2 -9)),((-18 8, 4 15, -1 -12, -13 18, 8 -17, -14 -19, -7 -13, 1 2, -11 -15, 5 20, 12 -14, 4 -10, -17 8, -6 15, -18 15)),((15 -2, 14 2, 17 -2, 6 3, -16 2),(7 0, 17 10, 17 -17, 13 -3, 1 -8)))"
    # txt_wkt = r"MULTIPOLYGON(((11 -17, -8 -1, 14 -8, 18 -17, 3 -11, 0 18, -17 -12, -17 -10, -10 -13)))"
    # txt_wkt = r"MULTIPOLYGON(((14 11, -14 -16, 16 18, 6 -8, -14 6, -20 -5, 12 -1, 2 -19, -15 10, 7 2)),((-16 -15, -16 -15, 19 -2, -2 -13, 3 -19, -16 14, -1 -20)),((0 2, -18 8, -20 17, 12 5, 13 17, -9 -8, -20 -8, 20 -6, -12 0, -9 -4, -5 -14, -16 -19)),((-15 -16, -14 2, 19 -18, 4 8, 18 -1, -2 -13)),((-10 9, -12 15, -16 20, -15 -13, -17 16, -11 3, 18 -13, -3 13, -6 1, 2 12)))"
    txt_wkt = r"MULTIPOLYGON(((14 7, -12 18, -13 -12, -7 19, 0 -16, 11 16, 19 18),(5 -11, -12 1, 0 -4, 1 -1)))"
    parser = Parser(txt_wkt)
    for index, multi_polygon in enumerate(parser.multi_polygons):
        print(f"multi_polygon {index} has {len(multi_polygon.polygons)} polygons")
        for i, p in enumerate(multi_polygon.polygons):
            print(f"  polygon {i} has {p.num_loops} loops")
