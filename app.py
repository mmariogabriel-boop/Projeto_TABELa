import hashlib
import io
import re
from datetime import date
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from proposta import (PRODUTOS, FAIXAS, acomodacoes, tabela_vazia, importar_tabela,
                      calcular, gerar_pdf, br, percentual, valor_para_edicao, colar_coluna)

st.set_page_config(page_title='Central de Propostas | Mediatorie', page_icon='📄', layout='wide')
components.html("""
<script>
(function() {
  const doc = window.parent.document;
  doc.documentElement.setAttribute('lang', 'pt-BR');
  doc.documentElement.setAttribute('translate', 'no');
  doc.documentElement.classList.add('notranslate');
  const meta = doc.createElement('meta');
  meta.name = 'google';
  meta.content = 'notranslate';
  if (!doc.querySelector('meta[name=\"google\"][content=\"notranslate\"]')) {
    doc.head.appendChild(meta);
  }
})();
</script>
""", height=0)
st.markdown('''<style>
.block-container{max-width:1180px;padding-top:2rem;padding-bottom:3rem}
.notranslate,[translate="no"]{translate:no}
[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.25);padding:16px;border-radius:12px;min-height:140px;display:flex;flex-direction:column;justify-content:center}
[data-testid="stMetricLabel"]{font-size:1rem}
[data-testid="stMetricValue"]{font-size:2.1rem;line-height:1.15}
[data-testid="stMetricValue"] > div{white-space:normal !important;overflow:visible !important;text-overflow:clip !important;word-break:break-word}
</style>''',unsafe_allow_html=True)
st.title('Central de Propostas Comerciais')
st.caption('MEDIATORIE  /  UNIMED VITÓRIA  ·  SAÚDE EMPRESARIAL  ·  v1.2')
st.caption('Interface fixada em português (Brasil). Se o navegador já tiver traduzido a página, atualize-a após instalar esta versão.')

with st.container(border=True):
    st.subheader('01  ·  Dados da proposta')
    c1,c2=st.columns(2)
    empresa=c1.text_input('Empresa *',max_chars=120)
    entidade=c2.text_input('Entidade *',max_chars=80)
    regime=c1.selectbox('Modalidade contratual',list(PRODUTOS))
    codigo=c2.selectbox('Produto',list(PRODUTOS[regime]),format_func=lambda c:f'{PRODUTOS[regime][c]} — {c}',key=f'prod_{regime}')
    produto=PRODUTOS[regime][codigo]
    c1,c2,c3=st.columns(3)
    reajuste=c1.text_input('Próximo reajuste *',placeholder='Ex.: Novembro/2027')
    local=c2.text_input('Local *',placeholder='Ex.: Vitória/ES')
    data=c3.date_input('Data da proposta',value=date.today(),format='DD/MM/YYYY')
    executivo=st.text_input('Executivo responsável (opcional)',max_chars=100)
    st.caption(f"O modelo informa reajuste contratual em {'novembro' if regime=='Compulsório' else 'dezembro'}. Confira a competência informada antes de emitir.")

with st.container(border=True):
    st.subheader('02  ·  Acomodação e desconto')
    st.markdown('<div class="notranslate" translate="no" lang="pt-BR"><strong>Acomodação</strong></div>', unsafe_allow_html=True)
    opcoes=acomodacoes(produto)
    escolha=st.radio('Acomodação',opcoes+(['Ambas'] if len(opcoes)==2 else []),horizontal=True,key=f'acom_{codigo}',label_visibility='collapsed') if len(opcoes)>1 else opcoes[0]
    if len(opcoes)==1: st.info(f'Acomodação: {escolha}')
    selecionadas=opcoes if escolha=='Ambas' else [escolha]
    comparar=False
    if escolha=='Ambas':
        comparar=st.radio('Como usar as duas acomodações?', ['Comparar as mesmas vidas nas duas opções','Distribuir vidas entre as duas acomodações'],key=f'modo_{codigo}') == 'Comparar as mesmas vidas nas duas opções'
    desconto=st.number_input('Desconto sobre a fatura bruta (%)',min_value=0.0,max_value=100.0,value=0.0,step=0.5,format='%.2f')

st.subheader('03  ·  Vidas e mensalidades por faixa etária')
st.caption('Informe os valores integrais, antes do desconto. Digite ou cole valores no formato brasileiro (315,93 ou 1.876,23). Também é possível importar Excel/CSV.')
st.download_button('Baixar planilha padrão (CSV)',tabela_vazia().to_csv(index=False,sep=';').encode('utf-8-sig'),'modelo_faixas.csv','text/csv')

def ler_arquivo(upload, prefixo):
    raw=upload.getvalue(); hdr=st.number_input('Linha do cabeçalho (1 = primeira linha)',min_value=1,max_value=100,value=1,step=1,key=prefixo+'_hdr')-1
    if upload.name.lower().endswith('.xlsx'):
        book=pd.ExcelFile(io.BytesIO(raw),engine='openpyxl')
        sheet=st.selectbox('Aba da planilha',book.sheet_names,key=prefixo+'_sheet')
        df=pd.read_excel(book,sheet_name=sheet,header=int(hdr),dtype=object)
    else:
        try: df=pd.read_csv(io.BytesIO(raw),sep=None,engine='python',header=int(hdr),dtype=object,encoding='utf-8-sig')
        except UnicodeDecodeError: df=pd.read_csv(io.BytesIO(raw),sep=None,engine='python',header=int(hdr),dtype=object,encoding='latin-1')
    df.columns=[str(c) for c in df.columns]
    return df

def escolher_coluna(label,cols,termos,key,opcional=False):
    options=[None]+cols if opcional else cols
    guess=next((c for c in cols if any(t in c.casefold() for t in termos)),None)
    idx=options.index(guess) if guess in options else 0
    return st.selectbox(label,options,index=idx,key=key,format_func=lambda v:'Não importar' if v is None else v)

def editar(acom,vidas_comuns=None):
    key=f'{regime}_{codigo}_{acom}_{comparar}'
    basekey=key+'_base'; versionkey=key+'_vers'; lastkey=key+'_last'
    if basekey not in st.session_state: st.session_state[basekey]=tabela_vazia(); st.session_state[versionkey]=0
    with st.container(border=True):
        st.markdown(f'<h4 class="notranslate" translate="no" lang="pt-BR">Acomodação: {acom}</h4>', unsafe_allow_html=True)
        if vidas_comuns is not None: st.caption('Quantidade de vidas copiada da enfermaria para comparação; informe somente as mensalidades de apartamento.')
        with st.expander('Importar arquivo Excel / CSV'):
            upload=st.file_uploader('Selecione o arquivo',type=['xlsx','csv'],key=key+'_upload')
            if upload:
                try:
                    df=ler_arquivo(upload,key)
                    st.dataframe(df.head(15),hide_index=True,use_container_width=True)
                    cols=list(df.columns)
                    faixa=escolher_coluna('Coluna de faixa etária',cols,['faixa','idade'],key+'_faixa')
                    vidas=None if vidas_comuns is not None else escolher_coluna('Coluna de beneficiários',cols,['benefici','vidas','quantidade'],key+'_vidas',True)
                    valor=escolher_coluna('Coluna de valor unitário',cols,['valor unit','mensalidade','tarifa'],key+'_valor',True)
                    if st.button('Aplicar importação',key=key+'_import'):
                        if vidas is None and valor is None: raise ValueError('Selecione pelo menos uma coluna de dados.')
                        if faixa in (vidas,valor) or (vidas is not None and vidas==valor): raise ValueError('Selecione colunas diferentes.')
                        base=st.session_state.get(lastkey,st.session_state[basekey])
                        tabela,ausentes=importar_tabela(df,faixa,vidas,valor,base)
                        st.session_state[basekey]=tabela;st.session_state[lastkey]=tabela.copy();st.session_state[versionkey]+=1
                        st.success('Dados importados. Confira a tabela abaixo.')
                        if ausentes: st.warning('Faixas não encontradas (valores anteriores mantidos): '+', '.join(ausentes))
                except Exception as e: st.error(f'Não foi possível importar: {e}')
        with st.expander('Colar dados diretamente do Excel'):
            st.caption('Copie somente as 10 células da coluna, de 00-18 até 59 ou mais, sem cabeçalho nem total. Uma célula vazia representa zero.')
            paste_cols=st.columns(2) if vidas_comuns is None else [None, st.container()]
            for painel, coluna, label, exemplo in zip(paste_cols, ['Beneficiários','Valor unitário'], ['Beneficiários','Mensalidades (R$)'], ['8\n3\n7\n...','315,93\n315,93\n770,88\n1.876,23\n...']):
                if painel is None: continue
                with painel:
                    sufixo='vidas' if coluna=='Beneficiários' else 'valores'
                    texto=st.text_area(label,placeholder=exemplo,height=180,key=key+'_colar_'+sufixo)
                    if st.button('Aplicar '+label.lower(),key=key+'_aplicar_'+sufixo):
                        try:
                            anterior=st.session_state.get(lastkey,st.session_state[basekey])
                            st.session_state[basekey]=colar_coluna(texto,coluna,anterior)
                            st.session_state[lastkey]=st.session_state[basekey].copy()
                            st.session_state[versionkey]+=1
                            st.success('Coluna preenchida. Confira os dados na tabela.')
                        except ValueError as e: st.error(str(e))
        if st.button('Limpar tabela',key=key+'_limpar'):
            st.session_state[basekey]=tabela_vazia();st.session_state[lastkey]=st.session_state[basekey].copy();st.session_state[versionkey]+=1
        base=st.session_state[basekey].copy()
        base['Valor unitário']=base['Valor unitário'].map(valor_para_edicao).astype(str)
        if vidas_comuns is not None: base['Beneficiários']=vidas_comuns
        edit=st.data_editor(base,hide_index=True,use_container_width=True,num_rows='fixed',key=key+'_editor_'+str(st.session_state[versionkey]),disabled=['Faixa Etária']+(['Beneficiários'] if vidas_comuns is not None else []),column_config={
            'Beneficiários':st.column_config.NumberColumn('Beneficiários',min_value=0,step=1,format='%d',required=True),
            'Valor unitário':st.column_config.TextColumn('Mensalidade integral (R$)',help='Formato brasileiro: 315,93 ou 1.876,23. Também aceita 315.93.',required=True),
        })
        if vidas_comuns is not None: edit['Beneficiários']=vidas_comuns
        st.session_state[lastkey]=edit.copy()
        return edit

entradas={};resultados={};erros=[]
for acom in selecionadas:
    comum=entradas['Enfermaria']['Beneficiários'].tolist() if comparar and acom=='Apartamento' else None
    entradas[acom]=editar(acom,comum)
    try:
        r=calcular(entradas[acom],desconto)
        if not r['vidas']: raise ValueError('Informe pelo menos um beneficiário.')
        resultados[acom]=r
        preview=pd.DataFrame({'Faixa Etária':FAIXAS,'Vidas':[l[0] for l in r['linhas']],'Mensalidade':[br(l[1]) for l in r['linhas']],'Fatura por faixa':[br(l[2]) for l in r['linhas']]})
        with st.expander(f'Conferir fatura por faixa · {acom}',expanded=True):
            st.dataframe(preview,hide_index=True,use_container_width=True)
    except ValueError as e:
        erros.append(f'{acom}: {e}');st.warning(erros[-1])

st.subheader('04  ·  Resultado da proposta')
def resumo(r):
    cols=st.columns(5)
    for col,label,val in zip(cols,['Vidas','Fatura bruta','Desconto mensal','Fatura líquida','Economia anual'],[r['vidas'],br(r['bruto']),br(r['economia']),br(r['liquido']),br(r['anual'])]): col.metric(label,val)
for acom,r in resultados.items():
    st.markdown(f'<div class="notranslate" translate="no" lang="pt-BR"><strong>{acom}</strong></div>', unsafe_allow_html=True);resumo(r)
if len(resultados)==2:
    if comparar: st.info('Cenários alternativos: não somar as vidas ou faturas das duas acomodações.')
    else:
        st.markdown('<div class="notranslate" translate="no" lang="pt-BR"><strong>Total combinado das acomodações</strong></div>', unsafe_allow_html=True);resumo({k:sum(r[k] for r in resultados.values()) for k in ['vidas','bruto','economia','liquido','anual']})
st.caption('Economia mensal = desconto sobre o preço integral; economia anual estimada = 12 × economia mensal, sem mudanças de carteira ou reajustes.')

st.subheader('05  ·  Gerar PDF')
faltantes=[n for n,v in [('Empresa',empresa),('Entidade',entidade),('Próximo reajuste',reajuste),('Local',local)] if not v.strip()]
if faltantes: st.caption('Campos obrigatórios pendentes: '+', '.join(faltantes))
dados=dict(empresa=empresa.strip(),entidade=entidade.strip(),reajuste=reajuste.strip(),local_data=f'{local.strip()}, {data:%d/%m/%Y}',executivo=executivo.strip(),regime=regime,codigo=codigo,modo=('Comparação de acomodações - mesmas vidas' if comparar else 'Vidas distribuídas por acomodação') if escolha=='Ambas' else '')
assinatura=hashlib.sha256(repr((dados,resultados)).encode()).hexdigest()
if st.button('Gerar proposta comercial',type='primary',disabled=bool(faltantes or erros or len(resultados)!=len(selecionadas)),use_container_width=True):
    try:
        pdf=gerar_pdf(dados,resultados)
        st.session_state['pdf_gerado']=(assinatura,pdf)
    except Exception as e: st.error(f'Erro ao gerar PDF: {e}')
if st.session_state.get('pdf_gerado',(None,None))[0]==assinatura and not faltantes and not erros:
    pdf=st.session_state['pdf_gerado'][1]
    st.success('Proposta gerada. O documento possui 12 páginas, com o produto selecionado.')
    nome=re.sub(r'[^\w-]+','_',empresa.strip()).strip('_')[:70] or 'empresa'
    st.download_button('Baixar proposta em PDF',pdf,f'Proposta_{nome}_{codigo}.pdf','application/pdf',use_container_width=True)
    with st.expander('Prévia da capa e da tabela'):
        import fitz
        with fitz.open(stream=pdf,filetype='pdf') as doc:
            a,b=st.columns(2)
            a.image(doc[0].get_pixmap(matrix=fitz.Matrix(1.3,1.3)).tobytes('png'),caption='Capa')
            b.image(doc[6].get_pixmap(matrix=fitz.Matrix(1.3,1.3)).tobytes('png'),caption='Tabela comercial')
