from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
import re
import unicodedata
import fitz
import pandas as pd

FAIXAS = ('00-18','19-23','24-28','29-33','34-38','39-43','44-48','49-53','54-58','59 ou mais')
PRODUTOS = {
    'Compulsório': {'7544':'Personal Ambulatorial','4369':'Personal Smart','0290':'Perfil Regional','7563':'Participativo Estadual','7565':'Premium Nacional'},
    'Livre Adesão': {'4327':'Personal Smart','0387':'Perfil Regional','4331':'Participativo Estadual','7826':'Premium Nacional','7834':'Vitoriamed'},
}
PAGINAS = {'Personal Ambulatorial':6,'Personal Smart':7,'Perfil Regional':8,'Participativo Estadual':9,'Premium Nacional':10,'Vitoriamed':11}
MODELO = Path(__file__).with_name('modelo.pdf')
CENT = Decimal('0.01')

def acomodacoes(produto):
    if produto == 'Personal Ambulatorial': return ['Ambulatorial']
    if produto == 'Personal Smart': return ['Enfermaria']
    return ['Enfermaria','Apartamento']

def decimal_br(v):
    """Lê valores brasileiros em texto ou números nativos, sem perder centavos."""
    if v is None or pd.isna(v): return Decimal(0)
    s = str(v).strip().replace('R$', '').replace('\xa0','').replace('\u202f','').replace(' ','')
    if not s: return Decimal(0)
    if isinstance(v, str):
        # Vírgula decimal brasileira: ponto só pode ser separador de milhares.
        if ',' in s:
            if not re.fullmatch(r'[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+),\d+', s):
                raise ValueError(f'Número inválido: {v}')
            s = s.replace('.', '').replace(',', '.')
        elif re.fullmatch(r'[+-]?\d{1,3}(?:\.\d{3})+', s):
            s = s.replace('.', '')
        elif not re.fullmatch(r'[+-]?\d+(?:\.\d+)?', s):
            raise ValueError(f'Número inválido: {v}')
    try: d = Decimal(s)
    except InvalidOperation: raise ValueError(f'Número inválido: {v}') from None
    if not d.is_finite() or d < 0: raise ValueError(f'Número negativo ou inválido: {v}')
    return d

def centavos(v): return v.quantize(CENT, rounding=ROUND_HALF_UP)

def br(v): return f'R$ {v:,.2f}'.replace(',','~').replace('.',',').replace('~','.')

def percentual(v): return f'{v:.2f}'.replace('.',',')+'%'

def tabela_vazia(): return pd.DataFrame({'Faixa Etária': FAIXAS,'Beneficiários':[0]*10,'Valor unitário':[0.0]*10})

def valor_para_edicao(v):
    # Preserva texto digitado (inclusive erros) até a validação do cálculo.
    if isinstance(v, str): return v
    return br(centavos(decimal_br(v))).removeprefix('R$ ')


def colar_coluna(texto, coluna, base):
    """Cola as dez células de uma única coluna na ordem oficial das faixas."""
    if coluna not in ('Beneficiários', 'Valor unitário'):
        raise ValueError('Coluna não suportada.')
    linhas = texto.replace('\r\n', '\n').replace('\r','\n').split('\n')
    # Excel geralmente termina a colagem com uma quebra de linha.
    if len(linhas) == len(FAIXAS)+1 and linhas[-1] == '': linhas.pop()
    if len(linhas) != len(FAIXAS):
        raise ValueError(f'Cole exatamente {len(FAIXAS)} células, uma por faixa etária. Recebidas: {len(linhas)}.')
    valores=[]
    for faixa, linha in zip(FAIXAS, linhas):
        if '\t' in linha or ';' in linha:
            raise ValueError('Cole somente uma coluna por vez, sem cabeçalho ou total.')
        try:
            n=decimal_br(linha)
            if coluna=='Beneficiários':
                if n != n.to_integral_value(): raise ValueError('Quantidade deve ser inteira.')
                valores.append(int(n))
            else: valores.append(br(centavos(n)).removeprefix('R$ '))
        except ValueError as e:
            raise ValueError(f'{faixa}: {e}') from None
    out=base.copy().reset_index(drop=True)
    if list(out['Faixa Etária'])!=list(FAIXAS): raise ValueError('Faixas etárias inválidas.')
    out[coluna]=valores
    return out


def normalizar_faixa(v):
    if pd.isna(v): return None
    s = unicodedata.normalize('NFKD',str(v).lower()).encode('ascii','ignore').decode()
    nums = re.findall(r'\d+',s)
    if nums and int(nums[0]) == 59 and len(nums)==1: return FAIXAS[-1]
    if len(nums)==2:
        for f in FAIXAS[:-1]:
            if list(map(int, f.split('-'))) == list(map(int,nums)): return f
    return None

def importar_tabela(df, faixa_col, vidas_col=None, valor_col=None, base=None):
    out = tabela_vazia() if base is None else base.copy().reset_index(drop=True)
    out['Valor unitário']=out['Valor unitário'].astype(object)
    encontrados=set()
    for _, row in df.iterrows():
        f = normalizar_faixa(row[faixa_col])
        if not f: continue  # ignora cabeçalhos auxiliares e totais
        if f in encontrados: raise ValueError(f'Faixa duplicada: {f}. Selecione uma tabela sem duplicidades.')
        encontrados.add(f); i=FAIXAS.index(f)
        if vidas_col is not None:
            n = decimal_br(row[vidas_col]);
            if n != n.to_integral_value(): raise ValueError(f'Quantidade fracionada em {f}.')
            out.loc[i,'Beneficiários']=int(n)
        if valor_col is not None: out.loc[i,'Valor unitário']=float(centavos(decimal_br(row[valor_col])))
    if not encontrados: raise ValueError('Não encontrei faixas etárias reconhecidas na coluna selecionada.')
    # Faixas não presentes mantêm os valores já digitados, ou zero em uma tabela nova.
    return out, [f for f in FAIXAS if f not in encontrados]

def calcular(df, desconto):
    d = decimal_br(desconto)
    if d > 100: raise ValueError('Desconto deve estar entre 0 e 100%.')
    linhas=[]
    if list(df['Faixa Etária']) != list(FAIXAS): raise ValueError('Faixas etárias inválidas.')
    for _, row in df.iterrows():
        try:
            n=decimal_br(row['Beneficiários']); u=centavos(decimal_br(row['Valor unitário']))
        except ValueError as e:
            raise ValueError(f"{row['Faixa Etária']}: {e}") from None
        if n != n.to_integral_value(): raise ValueError('Beneficiários devem ser números inteiros.')
        if n and not u: raise ValueError(f"Informe a mensalidade para {row['Faixa Etária']}.")
        linhas.append((int(n),u,centavos(n*u)))
    bruto=sum((l[2] for l in linhas),Decimal(0)); economia=centavos(bruto*d/100)
    return dict(linhas=linhas, vidas=sum(l[0] for l in linhas), bruto=bruto, desconto=d, economia=economia, liquido=bruto-economia, anual=economia*12)

def escrever(page, rect, valor, tamanho=10, cor=(0.12,0.16,0.12), bold=False):
    rect=fitz.Rect(rect); txt=str(valor); font='hebo' if bold else 'helv'
    if not txt: return
    while fitz.get_text_length(txt,fontname=font,fontsize=tamanho)>rect.width-4 and tamanho>5: tamanho-=0.25
    if fitz.get_text_length(txt,fontname=font,fontsize=tamanho)>rect.width-4: raise ValueError(f'Texto longo demais para o campo: {txt[:60]}')
    x=(rect.x0+rect.x1-fitz.get_text_length(txt,fontname=font,fontsize=tamanho))/2
    y=(rect.y0+rect.y1)/2+tamanho*0.34
    page.insert_text((x,y),txt,fontsize=tamanho,fontname=font,color=cor,overlay=True)

def mapa_tabela(page, dupla, lado):
    ws=list(page.widgets() or [])
    # Os nomes dos campos do modelo contêm inconsistências. A posição física é a referência.
    xs=(149,261,371) if not dupla else ((99,177,254) if lado==0 else (331,409,486))
    cols=[]
    for x in xs:
        group=sorted((w for w in ws if abs(w.rect.x0-x)<10 and not w.field_name.startswith('Economia')),key=lambda w:w.rect.y0)
        cols.append([fitz.Rect(w.rect) for w in group])
    if list(map(len,cols)) != [11,12,13]: raise ValueError('O modelo PDF não possui a estrutura de tabela esperada.')
    econ=sorted((w for w in ws if w.field_name.startswith('Economia') and (not dupla or (w.rect.x0<350)==(lado==0))),key=lambda w:w.rect.x0 if not dupla else w.rect.y0)
    if len(econ)!=2: raise ValueError('Campos de economia não encontrados.')
    return cols,[fitz.Rect(w.rect) for w in econ]

def gerar_pdf(dados, resultados, modelo=MODELO):
    regime, codigo = dados['regime'], dados['codigo']; produto=PRODUTOS[regime][codigo]; pagina=PAGINAS[produto]
    opcoes=acomodacoes(produto); dupla=len(opcoes)==2
    if not resultados or any(a not in opcoes for a in resultados): raise ValueError('Acomodação incompatível.')
    with fitz.open(modelo) as doc:
        if len(doc)!=17: raise ValueError('Modelo PDF inesperado.')
        capa=doc[0]
        rects={w.field_name:fitz.Rect(w.rect) for w in capa.widgets()}
        for w in list(capa.widgets()): capa.delete_widget(w)
        for campo,valor in [('Assinatura do responsável',dados['empresa']),('Entidade',dados['entidade']),('Próximo Reajuste',dados['reajuste']),('Local e Data',dados['local_data'])]:
            escrever(capa,rects[campo],valor,12,bold=True)
        escrever(capa,(311,592,543,617),dados.get('executivo',''),11)
        escrever(capa,(54,436,538,461),f'{regime.upper()} | {produto} - {codigo}',12,bold=True,cor=(0.25,0.43,0.19))
        escrever(capa,(54,645,538,668),dados.get('modo',''),10,cor=(0.25,0.43,0.19))
        pg=doc[pagina]; mapas=[mapa_tabela(pg,dupla,i) for i in range(len(opcoes))]
        for w in list(pg.widgets()): pg.delete_widget(w)
        for acomodacao,(cols,econ) in zip(opcoes,mapas):
            q,u,f=cols
            if acomodacao not in resultados:
                escrever(pg,q[0],'Não cotado',9,bold=True); continue
            r=resultados[acomodacao]
            for i,(n,unit,subtotal) in enumerate(r['linhas']):
                escrever(pg,q[i],n,9)
                escrever(pg,u[i],br(unit) if unit else '-',9)
                escrever(pg,f[i],br(subtotal),9)
            escrever(pg,q[10],r['vidas'],10,bold=True)
            escrever(pg,u[10],'-',10) # soma de mensalidades unitárias não é um total financeiro
            escrever(pg,f[10],br(r['bruto']),10,bold=True)
            escrever(pg,u[11],percentual(r['desconto']),10,bold=True)
            escrever(pg,f[11],br(r['economia']),10,bold=True)
            escrever(pg,f[12],br(r['liquido']),10,bold=True,cor=(1,1,1))
            escrever(pg,econ[0],br(r['economia']),9,bold=True)
            escrever(pg,econ[1],br(r['anual']),9,bold=True)
        doc.select(list(range(6))+[pagina]+list(range(12,17)))
        return doc.tobytes(garbage=4,deflate=True)
