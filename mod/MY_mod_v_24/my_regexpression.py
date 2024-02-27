import re
import ast


class RegularExpr:

    def len_multipolygon_in_wkt(self, wkt_str: str):
        """
        возвращает кол-во мультиполигонов в WKT геометрии (работает по кол-ву скобок)
            \(     ищем круглую скобку
            {2}    повторяется два раза
            [^\(]  кроме круглой скобки
            .*     любое количество любых символов
            (.*)   группировать
            (?:.*) так же группировать
            (.*?)  группировать без жадности
        """
        # паттерн поиска мультиполигонов
        patt_mult = r"(?:\({3}.*?\){3})"
        rslt_mult = re.findall(patt_mult, wkt_str)
        return len(rslt_mult)

    def len_polygon_in_wkt(self, wkt_str: str):
        """
        возвращает кол-во полигонов в WKT геометрии (работает по кол-ву скобок)
            \(     ищем круглую скобку
            {2}    повторяется два раза
            [^\(]  кроме круглой скобки
            .*     любое количество любых символов
            (.*)   группировать
            (?:.*) так же группировать
            (.*?)  группировать без жадности
        """
        # паттерн поиска полиогонов
        patt_poly = r"(?:\({2}.*?\){2})"
        rslt_path = re.findall(patt_poly, wkt_str)
        return len(rslt_path)

    def len_ring_in_polygons_wkt(self, wkt_str: str):
        """
        возвращает кол-во границ в полигоне по WKT геометрии (работает по кол-ву скобок)
            \(     ищем круглую скобку
            {2}    повторяется два раза
            [^\(]  кроме круглой скобки
            .*     любое количество любых символов
            (.*)   группировать
            (?:.*) так же группировать
            (.*?)  группировать без жадности
        """
        # паттерн поиска колец в полигоне
        patt_ring = r"(?:\({1}.*?\){1})"
        rslt_path = re.findall(patt_ring, wkt_str)
        return len(rslt_path)

    def get_dict_from_wkt(self, wkt_str: str) -> dict:
        """
        получаем из координат wkt мультиполигона словарь

        СТРУКТУРА СЛОВАРЯ:

        мультиполигон
                     полигон
                            кольца
                                  x - координаты
                                  y - координаты

        ПАМЯТКА для паттернов:
            \(     ищем круглую скобку
            {2}    повторяется два раза
            [^\(]  кроме круглой скобки
            .*     любое количество любых символов
            (.*)   группировать
            (?:.*) так же группировать
            (.*?)  группировать без жадности
        """
        # подключаем регулярку
        # паттерн поиска мультиполигонов
        patt_mult = r"(?:\({3}.*?\){3})"
        # паттерн поиска полиогонов
        patt_poly = r"(?:\({2}.*?\){2})"
        # паттерн поиска колец в полигоне
        patt_ring = r"(?:\({1}.*?\){1})"

        rslt_mult = re.findall(patt_mult, wkt_str)

        dic_rslt = {}
        # цикл по мультиполигонам)
        for x, mult in enumerate(rslt_mult):
            rslt_poly = re.findall(patt_poly, mult)

            poly_dic = {}
            # цикл по полигонам
            for y, poly in enumerate(rslt_poly):
                rslt_path = re.findall(patt_ring, poly)

                rng = {}
                # цикл по границам (ring)
                for z, pth in enumerate(rslt_path):

                    chr_replace = ['(', ')', ',']
                    for ch in chr_replace:
                        pth = pth.replace(ch, "")

                    pth = pth.split(' ')

                    x_crd = [v for k, v in enumerate(pth) if not k % 2]
                    y_crd = [v for k, v in enumerate(pth) if k % 2]

                    rng[z] = (x_crd, y_crd)

                poly_dic[y] = rng

            dic_rslt[x] = poly_dic

        return dic_rslt