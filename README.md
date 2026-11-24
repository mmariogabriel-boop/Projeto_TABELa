# Central de Propostas Comerciais — v2.1

Aplicação local em Streamlit para elaborar uma proposta comercial com um ou vários contratos, a partir do PDF original da Mediatorie / Unimed Vitória.

## Instalação e execução (Windows)

Extraia a pasta completa e execute `iniciar.bat`. O ambiente virtual fica em `%LOCALAPPDATA%\CentralPropostas\venv`, evitando caminhos longos no OneDrive. Se o navegador não abrir automaticamente, acesse http://localhost:8501. Alternativamente, execute `python -m pip install -r requirements.txt` e `python -m streamlit run app.py` em um ambiente virtual adequado.

## Como usar

1. Preencha empresa, local, data e executivo responsável (opcional).
2. Na área de contratos, preencha a entidade, próximo reajuste, referência opcional, modalidade, produto, acomodação e desconto de cada contrato.
3. Use **Adicionar contrato** para criar outro contrato. As abas permitem alternar entre eles. Cada contrato possui identificador interno próprio, inclusive quando o código do produto é repetido. **Remover contrato** exclui os dados do contrato selecionado da sessão.
4. Quando houver mais de um contrato, informe se são grupos distintos a contratar conjuntamente ou cenários alternativos. Não some as mesmas vidas em cenários diferentes.
5. Digite ou importe as vidas e tarifas por faixa etária, usando CSV/XLSX ou colando as dez células de uma coluna do Excel. O formato brasileiro (315,93; 1.876,23) é aceito. Confira os valores integrais antes do desconto.
6. Confira os resultados por contrato e o consolidado. Quando existir comparação de acomodações ou contratos alternativos, a proposta não exibe um total geral, evitando dupla contagem. Para somar grupos distintos, escolha distribuição de vidas, não comparação.
7. Gere e baixe o PDF. Uma única capa e as páginas institucionais/condições originais são mantidas. Para vários contratos, há uma página de produto por contrato, sem página de resumo no PDF. Cada página identifica número, modalidade, código, entidade, reajuste e referência (quando informada). Se entidade ou reajuste variar, a capa informa “Conforme contratos”. O consolidado permanece disponível na tela. Com apenas um contrato, conserva-se o formato anterior de 12 páginas.

## Regras e limites

- Uma empresa por proposta; entidades e reajustes podem variar por contrato.
- Desconto aplicado sobre a fatura bruta de cada acomodação; arredondamento em centavos. Economia anual = economia mensal × 12, sem mudanças na carteira ou reajustes.
- Não há cadastro de tarifas oficiais; informe os valores comerciais válidos.
- Dados mantidos na sessão do Streamlit; não há banco de dados nem recuperação após encerramento da sessão.
- As condições comerciais do PDF original permanecem inalteradas. Revise a elegibilidade de cada contrato e os reajustes antes de enviar.
- A interface sinaliza o idioma português ao navegador; se houver tradução automática ainda ativa, desative-a e recarregue a página.

## Arquivos

`app.py`: interface; `proposta.py`: cálculos, importação e PDF; `modelo.pdf`: modelo original usado no projeto; `requirements.txt`: dependências; `iniciar.bat`: inicializador; `test_proposta.py` e `test_multicontratos.py`: testes.

## Testes

Execute `python -m unittest discover -v` no ambiente virtual. Os 17 testes cobrem cálculos, formatos monetários, colagem, todos os produtos, contratos repetidos, modalidades mistas, totais, alternativas e paginação. A interface precisa ser validada no ambiente do usuário.
