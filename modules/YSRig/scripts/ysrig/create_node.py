import re
from maya import cmds

def connect_attr(src: list, dest: list, debug_print=False) -> None:
    """
    ノードのアトリビュートを接続する関数。
    """

    for s, d in zip(src, dest):
        if s is None:
            continue

        if isinstance(s, str): # 文字列型
            if "." in s: # アトリビュート接続
                if "!" == s[-1]: # 値の転写
                    s = s[:-1]
                    cmds.connectAttr(s, d, f=True)
                    cmds.disconnectAttr(s, d)
                    continue

                else:
                    cmds.connectAttr(s, d, f=True)
                    continue

            else:
                cmds.setAttr(d, s, type="string")
                continue

        elif isinstance(s, list) or isinstance(s, tuple): # リスト型、もしくはタプル型 => matrix型
            if "matrix" == cmds.getAttr(d, type=True):
                cmds.setAttr(d, s, type="matrix")

            else:
                node_name = d.split(".")[0]
                attr_path = d.split(".")[1]
                base_attr_name = re.sub(r"\[\d+\]$", "", attr_path)
                child_names = cmds.attributeQuery(base_attr_name, node=node_name, listChildren=True)
                for s_, d_ in zip(s, child_names):
                    if s_ is None:
                        continue

                    d_ = f"{node_name}.{attr_path}.{d_}"

                    if isinstance(s_, str):
                        if "." in s_:
                            if "!" == s_[-1]:
                                s_ = s_[:-1]
                                cmds.connectAttr(s_, d_, f=True)
                                cmds.disconnectAttr(s_, d_)
                                continue

                            else:
                                cmds.connectAttr(s_, d_, f=True)
                                continue

                        else:
                            cmds.setAttr(d_, s_, type="string")
                            continue

                    else:
                        cmds.setAttr(d_, s_)
                        continue

            continue

        else:
            cmds.setAttr(d, s)
            continue


def sort_out_attr(name :str, data: dict, debug_print=False):
    src = []
    dest = []

    if debug_print:
        print("---- input data ----\n")
        for d in data:
            value = data[d]["value"]
            if not value:
                if value is None or isinstance(value, list):
                    continue

            print(data[d])
        print("\n--------------------")

    for d in data:
        key = d[:]
        d = data[d]
        value = d["value"]
        attr = f'{name}.{d["attr"]}'
        _type = d["type"]
        inout = d["inout"]
        childern = d["childern"]

        if not value:
            if value is None or isinstance(value, list):
                continue

        if inout == "input":
            if _type == "other" or _type == "matrix":
                src += [value]
                dest += [attr]
                continue

            if _type == "multi":
                for i, v in enumerate(value):
                    src += [v]
                    dest += [f"{attr}[{i}]"]
                continue

            if _type == "compound":
                if isinstance(value, str):
                    src += [value]
                    dest += [attr]
                    continue

                if isinstance(value, list) or isinstance(value, tuple):
                    for c, v in zip(childern, value):
                        src += [v]
                        dest += [f"{name}.{c}"]
                    continue

        elif inout == "output":
            if _type == "other" or _type == "matrix":
                for v in value:
                    src += [attr]
                    dest += [v]
                continue

            if _type == "compound":
                if isinstance(value, str):
                    value = [value]

                for v in value:
                    if ":" in v:
                        for s_, v_ in zip(childern, v.split(":")[1:]):
                            src += [f"{name}.{s_}"]
                            dest += [f'{v.split(":")[0]}{v_}']

                    else:
                        src += [attr]
                        dest += [v]
                continue

        cmds.error(f"{key}アトリビュートの引数が正しく処理されませんでした。 attr:{attr}")

    if debug_print:
        print("---- sort data ----\n")
        for s, d in zip(src, dest):
            print(f"{s} -> {d}")

        print("\n-------------------")

    return src, dest



def generate_func():
    """
    選択したノードの、作成、接続、設定を行う関数を生成する関数。  
    ノードに対応した関数がprintされます。
    """

    node = cmds.ls(sl=True)[0]
    node_type = cmds.nodeType(node)
    long_attrs = cmds.listAttr(node)
    short_attrs = cmds.listAttr(node, sn=True)

    func = f'\n# ↓ function\n\ndef {node_type}(node_name :str="", debug_print :bool=False'

    comment = "        node_name (str): ノードの名前を設定します。\n"
    comment = "        debug_print (bool): デバッグプリントを表示します。\n"
    tags = []
    keys = []

    for la, sa in zip(long_attrs, short_attrs):
        try:
            if cmds.attributeQuery(la, node=node, writable=True):
                if len(la.split('.', 1)) != 1:
                    pass

                elif "matrix" == cmds.getAttr(f"{node}.{la}", type=True):
                    func += f', {sa}=None'
                    comment += f'        {sa} (any): {la} を設定します type="matrix"\n'
                    tags += [[sa, la, "matrix", "input", None]]
                    keys += [sa]

                elif cmds.attributeQuery(la, node=node, multi=True):
                    func += f', {sa} :list=[]'
                    comment += f'        {sa} (list[any]): {la} を設定します。type="multi"\n'
                    tags += [[sa, la, "multi", "input", None]]
                    keys += [sa]

                elif cmds.attributeQuery(la, node=node, listChildren=True):
                    func += f', {sa}=None'
                    comment += f'        {sa} (any): {la} を設定します。type="compound"\n'
                    tags += [[sa, la, "compound", "input", cmds.attributeQuery(la, node=node, listChildren=True)]]
                    keys += [sa]

                else:
                    func += f', {sa}=None'
                    comment += f'        {sa} (any): {la} を設定します。type="other"\n'
                    tags += [[sa, la, "other", "input", None]]
                    keys += [sa]

        except RuntimeError:
            continue

    for la, sa in zip(long_attrs, short_attrs):
        try:
            if cmds.attributeQuery(la, node=node, readable=True):
                if len(la.split('.', 1)) != 1:
                    pass

                elif cmds.attributeQuery(la, node=node, multi=True):
                    pass

                elif cmds.attributeQuery(la, node=node, listChildren=True):
                    func += f', {sa}_dest :list[str]=[]'
                    comment += f'        {sa}_dest (list): {la} の目的側のアトリビュートを設定します。type="compound"\n'
                    tags += [[f"{sa}_dest", la, "compound", "output", cmds.attributeQuery(la, node=node, listChildren=True)]]
                    keys += [f"{sa}_dest"]

                elif "matrix" == cmds.getAttr(f"{node}.{la}", type=True):
                    func += f', {sa}_dest :list[str]=[]'
                    comment += f'        {sa}_dest (list): {la} の目的側のアトリビュートを設定します。type="matrix"\n'
                    tags += [[f"{sa}_dest", la, "other", "output", None]]
                    keys += [f"{sa}_dest"]

                else:
                    func += f', {sa}_dest :list[str]=[]'
                    comment += f'        {sa}_dest (list): {la} の目的側のアトリビュートを設定します。type="other"\n'
                    tags += [[f"{sa}_dest", la, "other", "output", None]]
                    keys += [f"{sa}_dest"]

        except RuntimeError:
            continue

    func += ') -> str:\n    """\n'
    func += f'    {node_type}ノードを作成、接続、設定します。  \n'
    func += '    アトリビュートのショートネームが各フラグ名と対応しています。  \n'
    func += '    \n'
    func += '    "src.attr"の形で記述すると、そのアトリビュートと接続します。値を与えることで直接設定することもできます。  \n'
    func += f'    └ attr="src.attr" ... src.attr →接続→ {node_type}.attr  \n'
    func += f'    └ attr="3" ... 3 →設定→ {node_type}.attr  \n'
    func += '    \n'
    func += '    アトリビュート名の末尾に"!"をつけることで、そのアトリビュートの値を転写することができます。  \n'
    func += f'    └ attr="src.attr!" ... src.attr →転写→ {node_type}.attr  \n'
    func += '    \n'
    func += '    "multi型のアトリビュート(attr[0], attr[1], attr[2] のようにインデックスで管理するアトリビュート)の場合、引数はリスト型になります。  \n'
    func += '    Noneを設定すると、そのインデックスの設定はスキップされます。  \n'
    func += f'    └ mult_attr=["src1.attr", "src2.attr!", None, 3] ... src1.attr →接続→ {node_type}.attr[0], src2.attr →転写→ {node_type}.attr[1], 設定しない→ {node_type}.attr[2], 3 →設定→ {node_type}.attr[3]  \n'
    func += '    \n'
    func += '    "compound型のアトリビュート(vectorやangleのように複数のアトリビュートを複合したアトリビュート)の場合、接続の場合"src.attr"の形の文字列、値の設定の場合、リストで設定します。  \n'
    func += '    Noneを設定すると、その要素の設定はスキップされます。  \n'
    func += f'    └ vector_attr= "src.attr" ... src.attr →接続→ {node_type}.attr  \n'
    func += f'    └ vector_attr= [2, 4, 1] ... 2, 4, 1 →設定→ {node_type}.attrX, Y, Z  \n'
    func += f'    └ vector_attr= ["src.attrX", 4, None] ... src.attrX →接続→ {node_type}.attrX, 4 →設定→ {node_type}.attrY, 設定しない→ {node_type}.attrZ  \n'
    func += '    \n'
    func += '    "multi型の要素の一つとしてcompound型のアトリビュートが内包されている場合、それぞれの設定方法を複合します。  \n'
    func += f'    └ multi_attr= [[0, 1, 2], "src.vectorAttr", None, [src.attrX!, 3, None]]  \n'
    func += '    \n'
    func += '    ショートネームの末尾に"_dest"がついているフラグは、ノードに対して目的側のアトリビュートをリストで設定します。  \n'
    func += f'    └ attr_dest=["dest1.attr", dest2.attr] ... {node_type}.attr →接続→ dest1.attr, {node_type}.attr →接続→ dest2.attr  \n'
    func += '    \n'
    func += '    dest付きかつ、compound型のアトリビュート名の末尾に、":"をつけると、その後に続く文字を目的側アトリビュートにつけ足し、順次接続を実行します。  \n'
    func += f'    └ attr_dest=["dest.attr:X:Y:Z"] ... {node_type}.attrR →接続→ dest.attrX, {node_type}.attrG →接続→ dest.attrY, {node_type}.attrB →接続→ dest.attrZ  \n'
    func += f'    └ attr_dest=["dest.attr:[0]:[1]:[2]"] ... {node_type}.attrX →接続→ dest.attr[0], {node_type}.attrY →接続→ dest.attr[1], {node_type}.attrZ →接続→ dest.attr[2]  \n'
    func += '    \n'
    func += '    Args:\n'
    func += comment
    func += '    Returns:\n'
    func += '    \n'
    func += '        str : 作成されたノード名。\n'
    func += '    """\n'
    func += '    \n'
    func += f'    _node = cmds.createNode("{node_type}", name=node_name)\n'
    func += f'    cmds.setAttr(f"{{_node}}.isHistoricallyInteresting", 0)'
    func += '    \n'
    func += '    _data = {}\n'

    for key, tag in zip(keys, tags):
        func += f'    _data["{key}"] = {{"value":{tag[0]}, "attr":"{tag[1]}", "type":"{tag[2]}", "inout":"{tag[3]}", "childern":{tag[4]}}}\n'

    func += '    \n'
    func += '    _src, _dest = sort_out_attr(node_name, _data, debug_print=debug_print)\n'
    func += '    connect_attr(_src, _dest, debug_print=debug_print)\n'
    func += '    \n'
    func += f'    return _node'

    print(func)


def floatMath(node_name :str="", debug_print :bool=False, cch=None, fzn=None, ihi=None, nds=None, bnm=None, _fa=None, _fb=None, _cnd=None, msg_dest :list[str]=[], cch_dest :list[str]=[], fzn_dest :list[str]=[], ihi_dest :list[str]=[], nds_dest :list[str]=[], bnm_dest :list[str]=[], _fa_dest :list[str]=[], _fb_dest :list[str]=[], _cnd_dest :list[str]=[], of_dest :list[str]=[]) -> str:
    """
    floatMathノードを作成、接続、設定します。  
    アトリビュートのショートネームが各フラグ名と対応しています。  
    
    "src.attr"の形で記述すると、そのアトリビュートと接続します。値を与えることで直接設定することもできます。  
    └ attr="src.attr" ... src.attr →接続→ floatMath.attr  
    └ attr="3" ... 3 →設定→ floatMath.attr  
    
    アトリビュート名の末尾に"!"をつけることで、そのアトリビュートの値を転写することができます。  
    └ attr="src.attr!" ... src.attr →転写→ floatMath.attr  
    
    "multi型のアトリビュート(attr[0], attr[1], attr[2] のようにインデックスで管理するアトリビュート)の場合、引数はリスト型になります。  
    Noneを設定すると、そのインデックスの設定はスキップされます。  
    └ mult_attr=["src1.attr", "src2.attr!", None, 3] ... src1.attr →接続→ floatMath.attr[0], src2.attr →転写→ floatMath.attr[1], 設定しない→ floatMath.attr[2], 3 →設定→ floatMath.attr[3]  
    
    "compound型のアトリビュート(vectorやangleのように複数のアトリビュートを複合したアトリビュート)の場合、接続の場合"src.attr"の形の文字列、値の設定の場合、リストで設定します。  
    Noneを設定すると、その要素の設定はスキップされます。  
    └ vector_attr= "src.attr" ... src.attr →接続→ floatMath.attr  
    └ vector_attr= [2, 4, 1] ... 2, 4, 1 →設定→ floatMath.attrX, Y, Z  
    └ vector_attr= ["src.attrX", 4, None] ... src.attrX →接続→ floatMath.attrX, 4 →設定→ floatMath.attrY, 設定しない→ floatMath.attrZ  
    
    "multi型の要素の一つとしてcompound型のアトリビュートが内包されている場合、それぞれの設定方法を複合します。  
    └ multi_attr= [[0, 1, 2], "src.vectorAttr", None, [src.attrX!, 3, None]]  
    
    ショートネームの末尾に"_dest"がついているフラグは、ノードに対して目的側のアトリビュートをリストで設定します。  
    └ attr_dest=["dest1.attr", dest2.attr] ... floatMath.attr →接続→ dest1.attr, floatMath.attr →接続→ dest2.attr  
    
    dest付きかつ、compound型のアトリビュート名の末尾に、":"をつけると、その後に続く文字を目的側アトリビュートにつけ足し、順次接続を実行します。  
    └ attr_dest=["dest.attr:X:Y:Z"] ... floatMath.attrR →接続→ dest.attrX, floatMath.attrG →接続→ dest.attrY, floatMath.attrB →接続→ dest.attrZ  
    └ attr_dest=["dest.attr:[0]:[1]:[2]"] ... floatMath.attrX →接続→ dest.attr[0], floatMath.attrY →接続→ dest.attr[1], floatMath.attrZ →接続→ dest.attr[2]  
    
    Args:
        debug_print (bool): デバッグプリントを表示します。
        cch (any): caching を設定します。type="other"
        fzn (any): frozen を設定します。type="other"
        ihi (any): isHistoricallyInteresting を設定します。type="other"
        nds (any): nodeState を設定します。type="other"
        bnm (any): binMembership を設定します。type="other"
        _fa (any): floatA を設定します。type="other"
        _fb (any): floatB を設定します。type="other"
        _cnd (any): operation を設定します。type="other"
        msg_dest (list): message の目的側のアトリビュートを設定します。type="other"
        cch_dest (list): caching の目的側のアトリビュートを設定します。type="other"
        fzn_dest (list): frozen の目的側のアトリビュートを設定します。type="other"
        ihi_dest (list): isHistoricallyInteresting の目的側のアトリビュートを設定します。type="other"
        nds_dest (list): nodeState の目的側のアトリビュートを設定します。type="other"
        bnm_dest (list): binMembership の目的側のアトリビュートを設定します。type="other"
        _fa_dest (list): floatA の目的側のアトリビュートを設定します。type="other"
        _fb_dest (list): floatB の目的側のアトリビュートを設定します。type="other"
        _cnd_dest (list): operation の目的側のアトリビュートを設定します。type="other"
        of_dest (list): outFloat の目的側のアトリビュートを設定します。type="other"
    Returns:
    
        str : 作成されたノード名。
    """
    
    _node = cmds.createNode("floatMath", name=node_name)
    cmds.setAttr(f"{_node}.isHistoricallyInteresting", 0)    
    _data = {}
    _data["cch"] = {"value":cch, "attr":"caching", "type":"other", "inout":"input", "childern":None}
    _data["fzn"] = {"value":fzn, "attr":"frozen", "type":"other", "inout":"input", "childern":None}
    _data["ihi"] = {"value":ihi, "attr":"isHistoricallyInteresting", "type":"other", "inout":"input", "childern":None}
    _data["nds"] = {"value":nds, "attr":"nodeState", "type":"other", "inout":"input", "childern":None}
    _data["bnm"] = {"value":bnm, "attr":"binMembership", "type":"other", "inout":"input", "childern":None}
    _data["_fa"] = {"value":_fa, "attr":"floatA", "type":"other", "inout":"input", "childern":None}
    _data["_fb"] = {"value":_fb, "attr":"floatB", "type":"other", "inout":"input", "childern":None}
    _data["_cnd"] = {"value":_cnd, "attr":"operation", "type":"other", "inout":"input", "childern":None}
    _data["msg_dest"] = {"value":msg_dest, "attr":"message", "type":"other", "inout":"output", "childern":None}
    _data["cch_dest"] = {"value":cch_dest, "attr":"caching", "type":"other", "inout":"output", "childern":None}
    _data["fzn_dest"] = {"value":fzn_dest, "attr":"frozen", "type":"other", "inout":"output", "childern":None}
    _data["ihi_dest"] = {"value":ihi_dest, "attr":"isHistoricallyInteresting", "type":"other", "inout":"output", "childern":None}
    _data["nds_dest"] = {"value":nds_dest, "attr":"nodeState", "type":"other", "inout":"output", "childern":None}
    _data["bnm_dest"] = {"value":bnm_dest, "attr":"binMembership", "type":"other", "inout":"output", "childern":None}
    _data["_fa_dest"] = {"value":_fa_dest, "attr":"floatA", "type":"other", "inout":"output", "childern":None}
    _data["_fb_dest"] = {"value":_fb_dest, "attr":"floatB", "type":"other", "inout":"output", "childern":None}
    _data["_cnd_dest"] = {"value":_cnd_dest, "attr":"operation", "type":"other", "inout":"output", "childern":None}
    _data["of_dest"] = {"value":of_dest, "attr":"outFloat", "type":"other", "inout":"output", "childern":None}
    
    _src, _dest = sort_out_attr(node_name, _data, debug_print=debug_print)
    connect_attr(_src, _dest, debug_print=debug_print)
    
    return _node


def distanceBetween(node_name :str="", debug_print :bool=False, cch=None, fzn=None, ihi=None, nds=None, bnm=None, p1=None, p1x=None, p1y=None, p1z=None, im1=None, p2=None, p2x=None, p2y=None, p2z=None, im2=None, msg_dest :list[str]=[], cch_dest :list[str]=[], fzn_dest :list[str]=[], ihi_dest :list[str]=[], nds_dest :list[str]=[], bnm_dest :list[str]=[], d_dest :list[str]=[]) -> str:
    """
    distanceBetweenノードを作成、接続、設定します。  
    アトリビュートのショートネームが各フラグ名と対応しています。  
    
    "src.attr"の形で記述すると、そのアトリビュートと接続します。値を与えることで直接設定することもできます。  
    └ attr="src.attr" ... src.attr →接続→ distanceBetween.attr  
    └ attr="3" ... 3 →設定→ distanceBetween.attr  
    
    アトリビュート名の末尾に"!"をつけることで、そのアトリビュートの値を転写することができます。  
    └ attr="src.attr!" ... src.attr →転写→ distanceBetween.attr  
    
    "multi型のアトリビュート(attr[0], attr[1], attr[2] のようにインデックスで管理するアトリビュート)の場合、引数はリスト型になります。  
    Noneを設定すると、そのインデックスの設定はスキップされます。  
    └ mult_attr=["src1.attr", "src2.attr!", None, 3] ... src1.attr →接続→ distanceBetween.attr[0], src2.attr →転写→ distanceBetween.attr[1], 設定しない→ distanceBetween.attr[2], 3 →設定→ distanceBetween.attr[3]  
    
    "compound型のアトリビュート(vectorやangleのように複数のアトリビュートを複合したアトリビュート)の場合、接続の場合"src.attr"の形の文字列、値の設定の場合、リストで設定します。  
    Noneを設定すると、その要素の設定はスキップされます。  
    └ vector_attr= "src.attr" ... src.attr →接続→ distanceBetween.attr  
    └ vector_attr= [2, 4, 1] ... 2, 4, 1 →設定→ distanceBetween.attrX, Y, Z  
    └ vector_attr= ["src.attrX", 4, None] ... src.attrX →接続→ distanceBetween.attrX, 4 →設定→ distanceBetween.attrY, 設定しない→ distanceBetween.attrZ  
    
    "multi型の要素の一つとしてcompound型のアトリビュートが内包されている場合、それぞれの設定方法を複合します。  
    └ multi_attr= [[0, 1, 2], "src.vectorAttr", None, [src.attrX!, 3, None]]  
    
    ショートネームの末尾に"_dest"がついているフラグは、ノードに対して目的側のアトリビュートをリストで設定します。  
    └ attr_dest=["dest1.attr", dest2.attr] ... distanceBetween.attr →接続→ dest1.attr, distanceBetween.attr →接続→ dest2.attr  
    
    dest付きかつ、compound型のアトリビュート名の末尾に、":"をつけると、その後に続く文字を目的側アトリビュートにつけ足し、順次接続を実行します。  
    └ attr_dest=["dest.attr:X:Y:Z"] ... distanceBetween.attrR →接続→ dest.attrX, distanceBetween.attrG →接続→ dest.attrY, distanceBetween.attrB →接続→ dest.attrZ  
    └ attr_dest=["dest.attr:[0]:[1]:[2]"] ... distanceBetween.attrX →接続→ dest.attr[0], distanceBetween.attrY →接続→ dest.attr[1], distanceBetween.attrZ →接続→ dest.attr[2]  
    
    Args:
        debug_print (bool): デバッグプリントを表示します。
        cch (any): caching を設定します。type="other"
        fzn (any): frozen を設定します。type="other"
        ihi (any): isHistoricallyInteresting を設定します。type="other"
        nds (any): nodeState を設定します。type="other"
        bnm (any): binMembership を設定します。type="other"
        p1 (any): point1 を設定します。type="compound"
        p1x (any): point1X を設定します。type="other"
        p1y (any): point1Y を設定します。type="other"
        p1z (any): point1Z を設定します。type="other"
        im1 (any): inMatrix1 を設定します type="matrix"
        p2 (any): point2 を設定します。type="compound"
        p2x (any): point2X を設定します。type="other"
        p2y (any): point2Y を設定します。type="other"
        p2z (any): point2Z を設定します。type="other"
        im2 (any): inMatrix2 を設定します type="matrix"
        msg_dest (list): message の目的側のアトリビュートを設定します。type="other"
        cch_dest (list): caching の目的側のアトリビュートを設定します。type="other"
        fzn_dest (list): frozen の目的側のアトリビュートを設定します。type="other"
        ihi_dest (list): isHistoricallyInteresting の目的側のアトリビュートを設定します。type="other"
        nds_dest (list): nodeState の目的側のアトリビュートを設定します。type="other"
        bnm_dest (list): binMembership の目的側のアトリビュートを設定します。type="other"
        d_dest (list): distance の目的側のアトリビュートを設定します。type="other"
    Returns:
    
        str : 作成されたノード名。
    """
    
    _node = cmds.createNode("distanceBetween", name=node_name)
    cmds.setAttr(f"{_node}.isHistoricallyInteresting", 0)    
    _data = {}
    _data["cch"] = {"value":cch, "attr":"caching", "type":"other", "inout":"input", "childern":None}
    _data["fzn"] = {"value":fzn, "attr":"frozen", "type":"other", "inout":"input", "childern":None}
    _data["ihi"] = {"value":ihi, "attr":"isHistoricallyInteresting", "type":"other", "inout":"input", "childern":None}
    _data["nds"] = {"value":nds, "attr":"nodeState", "type":"other", "inout":"input", "childern":None}
    _data["bnm"] = {"value":bnm, "attr":"binMembership", "type":"other", "inout":"input", "childern":None}
    _data["p1"] = {"value":p1, "attr":"point1", "type":"compound", "inout":"input", "childern":['point1X', 'point1Y', 'point1Z']}
    _data["p1x"] = {"value":p1x, "attr":"point1X", "type":"other", "inout":"input", "childern":None}
    _data["p1y"] = {"value":p1y, "attr":"point1Y", "type":"other", "inout":"input", "childern":None}
    _data["p1z"] = {"value":p1z, "attr":"point1Z", "type":"other", "inout":"input", "childern":None}
    _data["im1"] = {"value":im1, "attr":"inMatrix1", "type":"matrix", "inout":"input", "childern":None}
    _data["p2"] = {"value":p2, "attr":"point2", "type":"compound", "inout":"input", "childern":['point2X', 'point2Y', 'point2Z']}
    _data["p2x"] = {"value":p2x, "attr":"point2X", "type":"other", "inout":"input", "childern":None}
    _data["p2y"] = {"value":p2y, "attr":"point2Y", "type":"other", "inout":"input", "childern":None}
    _data["p2z"] = {"value":p2z, "attr":"point2Z", "type":"other", "inout":"input", "childern":None}
    _data["im2"] = {"value":im2, "attr":"inMatrix2", "type":"matrix", "inout":"input", "childern":None}
    _data["msg_dest"] = {"value":msg_dest, "attr":"message", "type":"other", "inout":"output", "childern":None}
    _data["cch_dest"] = {"value":cch_dest, "attr":"caching", "type":"other", "inout":"output", "childern":None}
    _data["fzn_dest"] = {"value":fzn_dest, "attr":"frozen", "type":"other", "inout":"output", "childern":None}
    _data["ihi_dest"] = {"value":ihi_dest, "attr":"isHistoricallyInteresting", "type":"other", "inout":"output", "childern":None}
    _data["nds_dest"] = {"value":nds_dest, "attr":"nodeState", "type":"other", "inout":"output", "childern":None}
    _data["bnm_dest"] = {"value":bnm_dest, "attr":"binMembership", "type":"other", "inout":"output", "childern":None}
    _data["d_dest"] = {"value":d_dest, "attr":"distance", "type":"other", "inout":"output", "childern":None}
    
    _src, _dest = sort_out_attr(node_name, _data, debug_print=debug_print)
    connect_attr(_src, _dest, debug_print=debug_print)
    
    return _node


def decomposeMatrix(node_name :str="", debug_print :bool=False, cch=None, fzn=None, ihi=None, nds=None, bnm=None, imat=None, ro=None, msg_dest :list[str]=[], cch_dest :list[str]=[], fzn_dest :list[str]=[], ihi_dest :list[str]=[], nds_dest :list[str]=[], bnm_dest :list[str]=[], imat_dest :list[str]=[], ro_dest :list[str]=[], ot_dest :list[str]=[], otx_dest :list[str]=[], oty_dest :list[str]=[], otz_dest :list[str]=[], or_dest :list[str]=[], orx_dest :list[str]=[], ory_dest :list[str]=[], orz_dest :list[str]=[], os_dest :list[str]=[], osx_dest :list[str]=[], osy_dest :list[str]=[], osz_dest :list[str]=[], osh_dest :list[str]=[], oshx_dest :list[str]=[], oshy_dest :list[str]=[], oshz_dest :list[str]=[], oq_dest :list[str]=[], oqx_dest :list[str]=[], oqy_dest :list[str]=[], oqz_dest :list[str]=[], oqw_dest :list[str]=[]) -> str:
    """
    decomposeMatrixノードを作成、接続、設定します。  
    アトリビュートのショートネームが各フラグ名と対応しています。  
    
    "src.attr"の形で記述すると、そのアトリビュートと接続します。値を与えることで直接設定することもできます。  
    └ attr="src.attr" ... src.attr →接続→ decomposeMatrix.attr  
    └ attr="3" ... 3 →設定→ decomposeMatrix.attr  
    
    アトリビュート名の末尾に"!"をつけることで、そのアトリビュートの値を転写することができます。  
    └ attr="src.attr!" ... src.attr →転写→ decomposeMatrix.attr  
    
    "multi型のアトリビュート(attr[0], attr[1], attr[2] のようにインデックスで管理するアトリビュート)の場合、引数はリスト型になります。  
    Noneを設定すると、そのインデックスの設定はスキップされます。  
    └ mult_attr=["src1.attr", "src2.attr!", None, 3] ... src1.attr →接続→ decomposeMatrix.attr[0], src2.attr →転写→ decomposeMatrix.attr[1], 設定しない→ decomposeMatrix.attr[2], 3 →設定→ decomposeMatrix.attr[3]  
    
    "compound型のアトリビュート(vectorやangleのように複数のアトリビュートを複合したアトリビュート)の場合、接続の場合"src.attr"の形の文字列、値の設定の場合、リストで設定します。  
    Noneを設定すると、その要素の設定はスキップされます。  
    └ vector_attr= "src.attr" ... src.attr →接続→ decomposeMatrix.attr  
    └ vector_attr= [2, 4, 1] ... 2, 4, 1 →設定→ decomposeMatrix.attrX, Y, Z  
    └ vector_attr= ["src.attrX", 4, None] ... src.attrX →接続→ decomposeMatrix.attrX, 4 →設定→ decomposeMatrix.attrY, 設定しない→ decomposeMatrix.attrZ  
    
    "multi型の要素の一つとしてcompound型のアトリビュートが内包されている場合、それぞれの設定方法を複合します。  
    └ multi_attr= [[0, 1, 2], "src.vectorAttr", None, [src.attrX!, 3, None]]  
    
    ショートネームの末尾に"_dest"がついているフラグは、ノードに対して目的側のアトリビュートをリストで設定します。  
    └ attr_dest=["dest1.attr", dest2.attr] ... decomposeMatrix.attr →接続→ dest1.attr, decomposeMatrix.attr →接続→ dest2.attr  
    
    dest付きかつ、compound型のアトリビュート名の末尾に、":"をつけると、その後に続く文字を目的側アトリビュートにつけ足し、順次接続を実行します。  
    └ attr_dest=["dest.attr:X:Y:Z"] ... decomposeMatrix.attrR →接続→ dest.attrX, decomposeMatrix.attrG →接続→ dest.attrY, decomposeMatrix.attrB →接続→ dest.attrZ  
    └ attr_dest=["dest.attr:[0]:[1]:[2]"] ... decomposeMatrix.attrX →接続→ dest.attr[0], decomposeMatrix.attrY →接続→ dest.attr[1], decomposeMatrix.attrZ →接続→ dest.attr[2]  
    
    Args:
        debug_print (bool): デバッグプリントを表示します。
        cch (any): caching を設定します。type="other"
        fzn (any): frozen を設定します。type="other"
        ihi (any): isHistoricallyInteresting を設定します。type="other"
        nds (any): nodeState を設定します。type="other"
        bnm (any): binMembership を設定します。type="other"
        imat (any): inputMatrix を設定します type="matrix"
        ro (any): inputRotateOrder を設定します。type="other"
        msg_dest (list): message の目的側のアトリビュートを設定します。type="other"
        cch_dest (list): caching の目的側のアトリビュートを設定します。type="other"
        fzn_dest (list): frozen の目的側のアトリビュートを設定します。type="other"
        ihi_dest (list): isHistoricallyInteresting の目的側のアトリビュートを設定します。type="other"
        nds_dest (list): nodeState の目的側のアトリビュートを設定します。type="other"
        bnm_dest (list): binMembership の目的側のアトリビュートを設定します。type="other"
        imat_dest (list): inputMatrix の目的側のアトリビュートを設定します。type="matrix"
        ro_dest (list): inputRotateOrder の目的側のアトリビュートを設定します。type="other"
        ot_dest (list): outputTranslate の目的側のアトリビュートを設定します。type="compound"
        otx_dest (list): outputTranslateX の目的側のアトリビュートを設定します。type="other"
        oty_dest (list): outputTranslateY の目的側のアトリビュートを設定します。type="other"
        otz_dest (list): outputTranslateZ の目的側のアトリビュートを設定します。type="other"
        or_dest (list): outputRotate の目的側のアトリビュートを設定します。type="compound"
        orx_dest (list): outputRotateX の目的側のアトリビュートを設定します。type="other"
        ory_dest (list): outputRotateY の目的側のアトリビュートを設定します。type="other"
        orz_dest (list): outputRotateZ の目的側のアトリビュートを設定します。type="other"
        os_dest (list): outputScale の目的側のアトリビュートを設定します。type="compound"
        osx_dest (list): outputScaleX の目的側のアトリビュートを設定します。type="other"
        osy_dest (list): outputScaleY の目的側のアトリビュートを設定します。type="other"
        osz_dest (list): outputScaleZ の目的側のアトリビュートを設定します。type="other"
        osh_dest (list): outputShear の目的側のアトリビュートを設定します。type="compound"
        oshx_dest (list): outputShearX の目的側のアトリビュートを設定します。type="other"
        oshy_dest (list): outputShearY の目的側のアトリビュートを設定します。type="other"
        oshz_dest (list): outputShearZ の目的側のアトリビュートを設定します。type="other"
        oq_dest (list): outputQuat の目的側のアトリビュートを設定します。type="compound"
        oqx_dest (list): outputQuatX の目的側のアトリビュートを設定します。type="other"
        oqy_dest (list): outputQuatY の目的側のアトリビュートを設定します。type="other"
        oqz_dest (list): outputQuatZ の目的側のアトリビュートを設定します。type="other"
        oqw_dest (list): outputQuatW の目的側のアトリビュートを設定します。type="other"
    Returns:
    
        str : 作成されたノード名。
    """
    
    _node = cmds.createNode("decomposeMatrix", name=node_name)
    cmds.setAttr(f"{_node}.isHistoricallyInteresting", 0)    
    _data = {}
    _data["cch"] = {"value":cch, "attr":"caching", "type":"other", "inout":"input", "childern":None}
    _data["fzn"] = {"value":fzn, "attr":"frozen", "type":"other", "inout":"input", "childern":None}
    _data["ihi"] = {"value":ihi, "attr":"isHistoricallyInteresting", "type":"other", "inout":"input", "childern":None}
    _data["nds"] = {"value":nds, "attr":"nodeState", "type":"other", "inout":"input", "childern":None}
    _data["bnm"] = {"value":bnm, "attr":"binMembership", "type":"other", "inout":"input", "childern":None}
    _data["imat"] = {"value":imat, "attr":"inputMatrix", "type":"matrix", "inout":"input", "childern":None}
    _data["ro"] = {"value":ro, "attr":"inputRotateOrder", "type":"other", "inout":"input", "childern":None}
    _data["msg_dest"] = {"value":msg_dest, "attr":"message", "type":"other", "inout":"output", "childern":None}
    _data["cch_dest"] = {"value":cch_dest, "attr":"caching", "type":"other", "inout":"output", "childern":None}
    _data["fzn_dest"] = {"value":fzn_dest, "attr":"frozen", "type":"other", "inout":"output", "childern":None}
    _data["ihi_dest"] = {"value":ihi_dest, "attr":"isHistoricallyInteresting", "type":"other", "inout":"output", "childern":None}
    _data["nds_dest"] = {"value":nds_dest, "attr":"nodeState", "type":"other", "inout":"output", "childern":None}
    _data["bnm_dest"] = {"value":bnm_dest, "attr":"binMembership", "type":"other", "inout":"output", "childern":None}
    _data["imat_dest"] = {"value":imat_dest, "attr":"inputMatrix", "type":"other", "inout":"output", "childern":None}
    _data["ro_dest"] = {"value":ro_dest, "attr":"inputRotateOrder", "type":"other", "inout":"output", "childern":None}
    _data["ot_dest"] = {"value":ot_dest, "attr":"outputTranslate", "type":"compound", "inout":"output", "childern":['outputTranslateX', 'outputTranslateY', 'outputTranslateZ']}
    _data["otx_dest"] = {"value":otx_dest, "attr":"outputTranslateX", "type":"other", "inout":"output", "childern":None}
    _data["oty_dest"] = {"value":oty_dest, "attr":"outputTranslateY", "type":"other", "inout":"output", "childern":None}
    _data["otz_dest"] = {"value":otz_dest, "attr":"outputTranslateZ", "type":"other", "inout":"output", "childern":None}
    _data["or_dest"] = {"value":or_dest, "attr":"outputRotate", "type":"compound", "inout":"output", "childern":['outputRotateX', 'outputRotateY', 'outputRotateZ']}
    _data["orx_dest"] = {"value":orx_dest, "attr":"outputRotateX", "type":"other", "inout":"output", "childern":None}
    _data["ory_dest"] = {"value":ory_dest, "attr":"outputRotateY", "type":"other", "inout":"output", "childern":None}
    _data["orz_dest"] = {"value":orz_dest, "attr":"outputRotateZ", "type":"other", "inout":"output", "childern":None}
    _data["os_dest"] = {"value":os_dest, "attr":"outputScale", "type":"compound", "inout":"output", "childern":['outputScaleX', 'outputScaleY', 'outputScaleZ']}
    _data["osx_dest"] = {"value":osx_dest, "attr":"outputScaleX", "type":"other", "inout":"output", "childern":None}
    _data["osy_dest"] = {"value":osy_dest, "attr":"outputScaleY", "type":"other", "inout":"output", "childern":None}
    _data["osz_dest"] = {"value":osz_dest, "attr":"outputScaleZ", "type":"other", "inout":"output", "childern":None}
    _data["osh_dest"] = {"value":osh_dest, "attr":"outputShear", "type":"compound", "inout":"output", "childern":['outputShearX', 'outputShearY', 'outputShearZ']}
    _data["oshx_dest"] = {"value":oshx_dest, "attr":"outputShearX", "type":"other", "inout":"output", "childern":None}
    _data["oshy_dest"] = {"value":oshy_dest, "attr":"outputShearY", "type":"other", "inout":"output", "childern":None}
    _data["oshz_dest"] = {"value":oshz_dest, "attr":"outputShearZ", "type":"other", "inout":"output", "childern":None}
    _data["oq_dest"] = {"value":oq_dest, "attr":"outputQuat", "type":"compound", "inout":"output", "childern":['outputQuatX', 'outputQuatY', 'outputQuatZ', 'outputQuatW']}
    _data["oqx_dest"] = {"value":oqx_dest, "attr":"outputQuatX", "type":"other", "inout":"output", "childern":None}
    _data["oqy_dest"] = {"value":oqy_dest, "attr":"outputQuatY", "type":"other", "inout":"output", "childern":None}
    _data["oqz_dest"] = {"value":oqz_dest, "attr":"outputQuatZ", "type":"other", "inout":"output", "childern":None}
    _data["oqw_dest"] = {"value":oqw_dest, "attr":"outputQuatW", "type":"other", "inout":"output", "childern":None}
    
    _src, _dest = sort_out_attr(node_name, _data, debug_print=debug_print)
    connect_attr(_src, _dest, debug_print=debug_print)
    
    return _node


def condition(node_name :str="", debug_print :bool=False, cch=None, fzn=None, ihi=None, nds=None, bnm=None, op=None, ft=None, st=None, ct=None, ctr=None, ctg=None, ctb=None, cf=None, cfr=None, cfg=None, cfb=None, msg_dest :list[str]=[], cch_dest :list[str]=[], fzn_dest :list[str]=[], ihi_dest :list[str]=[], nds_dest :list[str]=[], bnm_dest :list[str]=[], op_dest :list[str]=[], ft_dest :list[str]=[], st_dest :list[str]=[], ct_dest :list[str]=[], ctr_dest :list[str]=[], ctg_dest :list[str]=[], ctb_dest :list[str]=[], cf_dest :list[str]=[], cfr_dest :list[str]=[], cfg_dest :list[str]=[], cfb_dest :list[str]=[], oc_dest :list[str]=[], ocr_dest :list[str]=[], ocg_dest :list[str]=[], ocb_dest :list[str]=[]) -> str:
    """
    conditionノードを作成、接続、設定します。  
    アトリビュートのショートネームが各フラグ名と対応しています。  
    
    "src.attr"の形で記述すると、そのアトリビュートと接続します。値を与えることで直接設定することもできます。  
    └ attr="src.attr" ... src.attr →接続→ condition.attr  
    └ attr="3" ... 3 →設定→ condition.attr  
    
    アトリビュート名の末尾に"!"をつけることで、そのアトリビュートの値を転写することができます。  
    └ attr="src.attr!" ... src.attr →転写→ condition.attr  
    
    "multi型のアトリビュート(attr[0], attr[1], attr[2] のようにインデックスで管理するアトリビュート)の場合、引数はリスト型になります。  
    Noneを設定すると、そのインデックスの設定はスキップされます。  
    └ mult_attr=["src1.attr", "src2.attr!", None, 3] ... src1.attr →接続→ condition.attr[0], src2.attr →転写→ condition.attr[1], 設定しない→ condition.attr[2], 3 →設定→ condition.attr[3]  
    
    "compound型のアトリビュート(vectorやangleのように複数のアトリビュートを複合したアトリビュート)の場合、接続の場合"src.attr"の形の文字列、値の設定の場合、リストで設定します。  
    Noneを設定すると、その要素の設定はスキップされます。  
    └ vector_attr= "src.attr" ... src.attr →接続→ condition.attr  
    └ vector_attr= [2, 4, 1] ... 2, 4, 1 →設定→ condition.attrX, Y, Z  
    └ vector_attr= ["src.attrX", 4, None] ... src.attrX →接続→ condition.attrX, 4 →設定→ condition.attrY, 設定しない→ condition.attrZ  
    
    "multi型の要素の一つとしてcompound型のアトリビュートが内包されている場合、それぞれの設定方法を複合します。  
    └ multi_attr= [[0, 1, 2], "src.vectorAttr", None, [src.attrX!, 3, None]]  
    
    ショートネームの末尾に"_dest"がついているフラグは、ノードに対して目的側のアトリビュートをリストで設定します。  
    └ attr_dest=["dest1.attr", dest2.attr] ... condition.attr →接続→ dest1.attr, condition.attr →接続→ dest2.attr  
    
    dest付きかつ、compound型のアトリビュート名の末尾に、":"をつけると、その後に続く文字を目的側アトリビュートにつけ足し、順次接続を実行します。  
    └ attr_dest=["dest.attr:X:Y:Z"] ... condition.attrR →接続→ dest.attrX, condition.attrG →接続→ dest.attrY, condition.attrB →接続→ dest.attrZ  
    └ attr_dest=["dest.attr:[0]:[1]:[2]"] ... condition.attrX →接続→ dest.attr[0], condition.attrY →接続→ dest.attr[1], condition.attrZ →接続→ dest.attr[2]  
    
    Args:
        debug_print (bool): デバッグプリントを表示します。
        cch (any): caching を設定します。type="other"
        fzn (any): frozen を設定します。type="other"
        ihi (any): isHistoricallyInteresting を設定します。type="other"
        nds (any): nodeState を設定します。type="other"
        bnm (any): binMembership を設定します。type="other"
        op (any): operation を設定します。type="other"
        ft (any): firstTerm を設定します。type="other"
        st (any): secondTerm を設定します。type="other"
        ct (any): colorIfTrue を設定します。type="compound"
        ctr (any): colorIfTrueR を設定します。type="other"
        ctg (any): colorIfTrueG を設定します。type="other"
        ctb (any): colorIfTrueB を設定します。type="other"
        cf (any): colorIfFalse を設定します。type="compound"
        cfr (any): colorIfFalseR を設定します。type="other"
        cfg (any): colorIfFalseG を設定します。type="other"
        cfb (any): colorIfFalseB を設定します。type="other"
        msg_dest (list): message の目的側のアトリビュートを設定します。type="other"
        cch_dest (list): caching の目的側のアトリビュートを設定します。type="other"
        fzn_dest (list): frozen の目的側のアトリビュートを設定します。type="other"
        ihi_dest (list): isHistoricallyInteresting の目的側のアトリビュートを設定します。type="other"
        nds_dest (list): nodeState の目的側のアトリビュートを設定します。type="other"
        bnm_dest (list): binMembership の目的側のアトリビュートを設定します。type="other"
        op_dest (list): operation の目的側のアトリビュートを設定します。type="other"
        ft_dest (list): firstTerm の目的側のアトリビュートを設定します。type="other"
        st_dest (list): secondTerm の目的側のアトリビュートを設定します。type="other"
        ct_dest (list): colorIfTrue の目的側のアトリビュートを設定します。type="compound"
        ctr_dest (list): colorIfTrueR の目的側のアトリビュートを設定します。type="other"
        ctg_dest (list): colorIfTrueG の目的側のアトリビュートを設定します。type="other"
        ctb_dest (list): colorIfTrueB の目的側のアトリビュートを設定します。type="other"
        cf_dest (list): colorIfFalse の目的側のアトリビュートを設定します。type="compound"
        cfr_dest (list): colorIfFalseR の目的側のアトリビュートを設定します。type="other"
        cfg_dest (list): colorIfFalseG の目的側のアトリビュートを設定します。type="other"
        cfb_dest (list): colorIfFalseB の目的側のアトリビュートを設定します。type="other"
        oc_dest (list): outColor の目的側のアトリビュートを設定します。type="compound"
        ocr_dest (list): outColorR の目的側のアトリビュートを設定します。type="other"
        ocg_dest (list): outColorG の目的側のアトリビュートを設定します。type="other"
        ocb_dest (list): outColorB の目的側のアトリビュートを設定します。type="other"
    Returns:
    
        str : 作成されたノード名。
    """
    
    _node = cmds.createNode("condition", name=node_name)
    cmds.setAttr(f"{_node}.isHistoricallyInteresting", 0)    
    _data = {}
    _data["cch"] = {"value":cch, "attr":"caching", "type":"other", "inout":"input", "childern":None}
    _data["fzn"] = {"value":fzn, "attr":"frozen", "type":"other", "inout":"input", "childern":None}
    _data["ihi"] = {"value":ihi, "attr":"isHistoricallyInteresting", "type":"other", "inout":"input", "childern":None}
    _data["nds"] = {"value":nds, "attr":"nodeState", "type":"other", "inout":"input", "childern":None}
    _data["bnm"] = {"value":bnm, "attr":"binMembership", "type":"other", "inout":"input", "childern":None}
    _data["op"] = {"value":op, "attr":"operation", "type":"other", "inout":"input", "childern":None}
    _data["ft"] = {"value":ft, "attr":"firstTerm", "type":"other", "inout":"input", "childern":None}
    _data["st"] = {"value":st, "attr":"secondTerm", "type":"other", "inout":"input", "childern":None}
    _data["ct"] = {"value":ct, "attr":"colorIfTrue", "type":"compound", "inout":"input", "childern":['colorIfTrueR', 'colorIfTrueG', 'colorIfTrueB']}
    _data["ctr"] = {"value":ctr, "attr":"colorIfTrueR", "type":"other", "inout":"input", "childern":None}
    _data["ctg"] = {"value":ctg, "attr":"colorIfTrueG", "type":"other", "inout":"input", "childern":None}
    _data["ctb"] = {"value":ctb, "attr":"colorIfTrueB", "type":"other", "inout":"input", "childern":None}
    _data["cf"] = {"value":cf, "attr":"colorIfFalse", "type":"compound", "inout":"input", "childern":['colorIfFalseR', 'colorIfFalseG', 'colorIfFalseB']}
    _data["cfr"] = {"value":cfr, "attr":"colorIfFalseR", "type":"other", "inout":"input", "childern":None}
    _data["cfg"] = {"value":cfg, "attr":"colorIfFalseG", "type":"other", "inout":"input", "childern":None}
    _data["cfb"] = {"value":cfb, "attr":"colorIfFalseB", "type":"other", "inout":"input", "childern":None}
    _data["msg_dest"] = {"value":msg_dest, "attr":"message", "type":"other", "inout":"output", "childern":None}
    _data["cch_dest"] = {"value":cch_dest, "attr":"caching", "type":"other", "inout":"output", "childern":None}
    _data["fzn_dest"] = {"value":fzn_dest, "attr":"frozen", "type":"other", "inout":"output", "childern":None}
    _data["ihi_dest"] = {"value":ihi_dest, "attr":"isHistoricallyInteresting", "type":"other", "inout":"output", "childern":None}
    _data["nds_dest"] = {"value":nds_dest, "attr":"nodeState", "type":"other", "inout":"output", "childern":None}
    _data["bnm_dest"] = {"value":bnm_dest, "attr":"binMembership", "type":"other", "inout":"output", "childern":None}
    _data["op_dest"] = {"value":op_dest, "attr":"operation", "type":"other", "inout":"output", "childern":None}
    _data["ft_dest"] = {"value":ft_dest, "attr":"firstTerm", "type":"other", "inout":"output", "childern":None}
    _data["st_dest"] = {"value":st_dest, "attr":"secondTerm", "type":"other", "inout":"output", "childern":None}
    _data["ct_dest"] = {"value":ct_dest, "attr":"colorIfTrue", "type":"compound", "inout":"output", "childern":['colorIfTrueR', 'colorIfTrueG', 'colorIfTrueB']}
    _data["ctr_dest"] = {"value":ctr_dest, "attr":"colorIfTrueR", "type":"other", "inout":"output", "childern":None}
    _data["ctg_dest"] = {"value":ctg_dest, "attr":"colorIfTrueG", "type":"other", "inout":"output", "childern":None}
    _data["ctb_dest"] = {"value":ctb_dest, "attr":"colorIfTrueB", "type":"other", "inout":"output", "childern":None}
    _data["cf_dest"] = {"value":cf_dest, "attr":"colorIfFalse", "type":"compound", "inout":"output", "childern":['colorIfFalseR', 'colorIfFalseG', 'colorIfFalseB']}
    _data["cfr_dest"] = {"value":cfr_dest, "attr":"colorIfFalseR", "type":"other", "inout":"output", "childern":None}
    _data["cfg_dest"] = {"value":cfg_dest, "attr":"colorIfFalseG", "type":"other", "inout":"output", "childern":None}
    _data["cfb_dest"] = {"value":cfb_dest, "attr":"colorIfFalseB", "type":"other", "inout":"output", "childern":None}
    _data["oc_dest"] = {"value":oc_dest, "attr":"outColor", "type":"compound", "inout":"output", "childern":['outColorR', 'outColorG', 'outColorB']}
    _data["ocr_dest"] = {"value":ocr_dest, "attr":"outColorR", "type":"other", "inout":"output", "childern":None}
    _data["ocg_dest"] = {"value":ocg_dest, "attr":"outColorG", "type":"other", "inout":"output", "childern":None}
    _data["ocb_dest"] = {"value":ocb_dest, "attr":"outColorB", "type":"other", "inout":"output", "childern":None}
    
    _src, _dest = sort_out_attr(node_name, _data, debug_print=debug_print)
    connect_attr(_src, _dest, debug_print=debug_print)
    
    return _node
