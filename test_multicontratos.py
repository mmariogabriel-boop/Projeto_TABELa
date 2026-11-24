import unittest
from decimal import Decimal
import fitz
from proposta import *

class MultiTests(unittest.TestCase):
    def setUp(self):
        self.dados=dict(empresa='Empresa Exemplo',local_data='Vitória, 24/11/2026',executivo='Executivo Exemplo')
        t=tabela_vazia();t['Beneficiários']=[8,3,7,5,5,3,7,2,2,0];t['Valor unitário']=['315,93']*6+['770,88']*3+['1.876,23']
        self.r=calcular(t,'13,91')
        t=tabela_vazia();t.loc[0,'Beneficiários']=15;t.loc[0,'Valor unitário']=200
        self.r2=calcular(t,10)
        self.a=dict(regime='Compulsório',codigo='7563',entidade='Entidade A',reajuste='Novembro/2027',referencia='A001',comparar=False,resultados={'Enfermaria':self.r})
        self.b=dict(regime='Livre Adesão',codigo='4327',entidade='Entidade B',reajuste='Dezembro/2027',referencia='B002',comparar=False,resultados={'Enfermaria':self.r2})
    def test_total(self):
        t=totalizar_contratos([self.a,self.b]);self.assertEqual(t['vidas'],57);self.assertEqual(t['bruto'],Decimal('21273.51'));self.assertEqual(t['economia'],Decimal('2841.85'));self.assertEqual(t['liquido'],Decimal('18431.66'));self.assertEqual(t['anual'],Decimal('34102.20'))
    def test_pdf_misto(self):
        pdf=gerar_pdf_contratos(self.dados,[self.a,self.b]);
        with fitz.open(stream=pdf,filetype='pdf') as doc:
            self.assertEqual(len(doc),13)
            self.assertIn('2 CONTRATOS',doc[0].get_text());self.assertIn('Conforme contratos',doc[0].get_text())
            self.assertNotIn('RESUMO DOS CONTRATOS',''.join(p.get_text() for p in doc));self.assertIn('Entidade B',doc[7].get_text());self.assertIn('B002',doc[7].get_text());self.assertIn('Dezembro/2027',doc[7].get_text())
            self.assertIn('7563',doc[6].get_text());self.assertIn('15.731,66',doc[6].get_text());self.assertIn('4327',doc[7].get_text());self.assertIn('2.700,00',doc[7].get_text())
    def test_repeticao_produto(self):
        b={**self.a,'resultados':{'Enfermaria':self.r2}}
        with fitz.open(stream=gerar_pdf_contratos(self.dados,[self.a,b]),filetype='pdf') as doc:
            self.assertIn('15.731,66',doc[6].get_text());self.assertIn('2.700,00',doc[7].get_text());self.assertIn('Contrato 02',doc[7].get_text())
    def test_alternativos(self):
        self.assertIsNone(totalizar_contratos([self.a,self.b],False))
        with fitz.open(stream=gerar_pdf_contratos(self.dados,[self.a,self.b],False),filetype='pdf') as doc:
            self.assertIn('não somar',doc[6].get_text());self.assertNotIn('TOTAL CONSOLIDADO',doc[6].get_text())
    def test_comparar(self):
        a={**self.a,'comparar':True,'resultados':{'Enfermaria':self.r,'Apartamento':self.r}}
        self.assertIsNone(totalizar_contratos([a,self.b]))
        with fitz.open(stream=gerar_pdf_contratos(self.dados,[a,self.b]),filetype='pdf') as doc:
            self.assertIn('mesmas vidas',doc[6].get_text());self.assertNotIn('RESUMO DOS CONTRATOS',doc[6].get_text())
        with self.assertRaises(ValueError): gerar_pdf_contratos(self.dados,[{**a,'resultados':{'Enfermaria':self.r,'Apartamento':self.r2}}])
    def test_paginacao(self):
        with fitz.open(stream=gerar_pdf_contratos(self.dados,[self.a]*5),filetype='pdf') as doc:
            self.assertEqual(len(doc),16);self.assertIn('Contrato 01',doc[6].get_text());self.assertIn('Contrato 05',doc[10].get_text())
    def test_unitario(self):
        with fitz.open(stream=gerar_pdf_contratos(self.dados,[self.a]),filetype='pdf') as doc:
            self.assertEqual(len(doc),12);self.assertIn('7563',doc[0].get_text());self.assertIn('A001',doc[0].get_text())
    def test_invalido(self):
        for c in [{**self.a,'entidade':''},{**self.a,'resultados':{}},{**self.a,'codigo':'4327'}]:
            with self.assertRaises(ValueError): gerar_pdf_contratos(self.dados,[c])
