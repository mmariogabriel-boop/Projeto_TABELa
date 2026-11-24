import unittest
from decimal import Decimal
import pandas as pd
import fitz
from proposta import *

class PropostaTests(unittest.TestCase):
    def setUp(self):
        self.t=tabela_vazia()
        self.t['Beneficiários']=[8,3,7,5,5,3,7,2,2,0]
        self.t['Valor unitário']=[200+i*50 for i in range(10)]
    def test_calculo(self):
        r=calcular(self.t,10)
        self.assertEqual(r['vidas'],42)
        self.assertEqual(r['bruto'],Decimal('15350.00'))
        self.assertEqual(r['economia'],Decimal('1535.00'))
        self.assertEqual(r['liquido'],Decimal('13815.00'))
        self.assertEqual(r['anual'],Decimal('18420.00'))
    def test_importacao(self):
        src=pd.DataFrame({'Idade':['0 a 18','59 ou +','Total'],'7563':[8,None,8],'Tarifa':['R$ 1.200,50','200,00','']})
        t,missing=importar_tabela(src,'Idade','7563','Tarifa')
        self.assertEqual(t.iloc[0]['Beneficiários'],8)
        self.assertEqual(t.iloc[0]['Valor unitário'],1200.5)
        self.assertEqual(len(missing),8)
    def test_formatos_monetarios(self):
        for texto, esperado in [('315,93','315.93'),('770,88','770.88'),('1.876,23','1876.23'),('R$ 1.876,23','1876.23'),('315.93','315.93'),(315.93,'315.93')]:
            with self.subTest(texto=texto):
                self.assertEqual(decimal_br(texto),Decimal(esperado))
        for texto in ['1,2,3','1.2,34','texto','-5']:
            with self.assertRaises(ValueError): decimal_br(texto)
    def test_colagem_excel(self):
        t=colar_coluna('8\r\n3\r\n7\r\n5\r\n5\r\n3\r\n7\r\n2\r\n2\r\n0\r\n','Beneficiários',tabela_vazia())
        t=colar_coluna('\n'.join(['315,93']*6+['770,88']*3+['1.876,23']),'Valor unitário',t)
        self.assertEqual(t['Valor unitário'].tolist(),['315,93']*6+['770,88']*3+['1.876,23'])
        r=calcular(t,'13,91')
        self.assertEqual(r['vidas'],42)
        self.assertEqual(r['bruto'],Decimal('18273.51'))
        self.assertEqual(r['economia'],Decimal('2541.85'))
        self.assertEqual(r['liquido'],Decimal('15731.66'))
        self.assertEqual(r['anual'],Decimal('30502.20'))
        dados=dict(regime='Compulsório',codigo='7563',empresa='Empresa Teste',entidade='Entidade Teste',reajuste='2027',local_data='Vitória, 24/11/2026',executivo='')
        with fitz.open(stream=gerar_pdf(dados,{'Enfermaria':r}),filetype='pdf') as doc:
            txt=doc[6].get_text()
            for valor in ['315,93','770,88','1.876,23','15.731,66']: self.assertIn(valor,txt)
    def test_colagem_invalida(self):
        for texto in ['315,93','\n'.join(['315,93\t770,88']*10),'\n'.join(['x']*10)]:
            with self.assertRaises(ValueError): colar_coluna(texto,'Valor unitário',tabela_vazia())
    def test_importacao_preserva_texto_editado(self):
        base=tabela_vazia();base['Valor unitário']=['315,93']*10
        t,_=importar_tabela(pd.DataFrame({'faixa':['00-18'],'tarifa':[770.88]}),'faixa',valor_col='tarifa',base=base)
        self.assertEqual(t['Valor unitário'].map(valor_para_edicao).tolist(),['770,88']+['315,93']*9)
    def test_sem_tarifa(self):
        t=tabela_vazia();t.loc[0,'Beneficiários']=1
        with self.assertRaises(ValueError): calcular(t,10)
    def test_percentual_invalido(self):
        with self.assertRaises(ValueError): calcular(self.t,101)
    def test_todos_produtos(self):
        r=calcular(self.t,10)
        for regime,produtos in PRODUTOS.items():
            for codigo,produto in produtos.items():
                with self.subTest(codigo=codigo):
                    dados=dict(regime=regime,codigo=codigo,empresa='Empresa Teste',entidade='Entidade Teste',reajuste='2027',local_data='Vitória, 24/11/2026',executivo='')
                    acoms=acomodacoes(produto)
                    casos=[{a:r} for a in acoms]
                    if len(acoms)==2: casos.append({a:r for a in acoms})
                    for caso in casos:
                        with fitz.open(stream=gerar_pdf(dados,caso),filetype='pdf') as doc:
                            self.assertEqual(len(doc),12)
                            self.assertIn(codigo,doc[0].get_text())
                            self.assertIn('13.815,00',doc[6].get_text())
                            self.assertEqual(len(list(doc[6].widgets() or [])),0)
                            if len(acoms)==2 and len(caso)==1: self.assertIn('Não cotado',doc[6].get_text())
if __name__=='__main__': unittest.main()
