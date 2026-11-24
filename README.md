# Central de Propostas Comerciais — Mediatorie (v1.1)

Aplicação Streamlit para preencher o PDF original de propostas de saúde da Mediatorie/Unimed Vitória.

## Iniciar no Windows

1. Extraia todo o ZIP para uma pasta local.
2. Instale Python 3.11 ou 3.12, caso ainda não tenha instalado (adicione ao PATH).
3. Execute `iniciar.bat`. O script cria um ambiente virtual em `%LOCALAPPDATA%\CentralPropostas\venv`, fora do OneDrive, e instala as dependências; a primeira instalação exige internet.
4. O Streamlit abre no navegador (normalmente http://localhost:8501). Mantenha o terminal aberto durante o uso.

Ou execute no terminal, dentro da pasta:

```
python -m venv "%LOCALAPPDATA%\CentralPropostas\venv"
"%LOCALAPPDATA%\CentralPropostas\venv\Scripts\python.exe" -m pip install -r requirements.txt
"%LOCALAPPDATA%\CentralPropostas\venv\Scripts\python.exe" -m streamlit run app.py
```

## Como usar

Preencha os dados da empresa, selecione regime e código, acomodações e desconto. Informe vidas e mensalidades integrais por faixa etária. Você pode digitar diretamente ou importar Excel (.xlsx) / CSV. Baixe o CSV padrão na própria aplicação se preferir.

Para uma planilha com múltiplas colunas, selecione a aba, a linha do cabeçalho e as colunas correspondentes à faixa, vidas e valor unitário. Exemplo: para colunas duplicadas de enfermaria/apartamento, selecione cada uma no painel da acomodação correspondente. O importador ignora linhas sem faixa reconhecida (incluindo total); faixas ausentes mantêm valores anteriores e geram aviso. Revise a tabela. Não há reconhecimento automático de preços por código. Para carregar vidas e valores de arquivos diferentes, importe uma coluna de cada vez, usando “Não importar” na outra.

Na seção 03, abra “Colar dados diretamente do Excel”, copie exatamente as dez células de uma coluna (sem cabeçalho ou total), cole e clique em Aplicar. A coluna de mensalidades é textual para preservar a vírgula decimal. A conferência da fatura por faixa aparece logo abaixo. Se o navegador modificar termos como Enfermaria e Acomodação, desative a tradução automática da página.

Os valores devem ser numéricos ou no formato brasileiro (ex.: R$ 1.234,56). Valores unitários são arredondados a centavos. O sistema bloqueia faturas de faixas com vidas e mensalidade zero. A cotação de ambas pode comparar a mesma carteira (sem somar opções) ou distribuir vidas entre duas acomodações. O percentual de desconto é comum às opções.

## Cálculo e PDF

- Fatura por faixa = vidas × mensalidade integral.
- Fatura bruta = soma das faturas por faixa.
- Economia mensal = fatura bruta × desconto / 100, arredondada a centavos.
- Fatura líquida = fatura bruta − economia mensal.
- Economia anual estimada = economia mensal × 12, sem mudanças de carteira/reajustes. Não é uma comparação contra a fatura de outra operadora.
- A soma de preços unitários não é um total financeiro; a célula de total de mensalidades recebe um traço.
- O PDF mantém capa, páginas institucionais, produto selecionado e condições finais (12 páginas); acomodações não escolhidas recebem “Não cotado”. Os valores são gravados como texto estático no PDF para preservar a apresentação. O modelo original não é modificado.
- O rodapé original informa reajuste contratual em novembro (Compulsório) e dezembro (Livre Adesão); confira a data preenchida na capa.

Não foram fornecidas tarifas oficiais. Não há preços comerciais cadastrados nem histórico persistente de propostas, login ou banco de dados nesta versão local. Os dados ficam na sessão do Streamlit até o encerramento/reinício. Não publique a aplicação sem revisar controle de acesso e termos de licenciamento das dependências (incluindo PyMuPDF).

## Arquivos

- `app.py`: interface e importação de planilhas.
- `proposta.py`: regras, cálculos e preenchimento do PDF.
- `modelo.pdf`: original enviado.
- `requirements.txt`: dependências.
- `iniciar.bat`: inicializador Windows.
- `.streamlit/config.toml`: tema.
- `test_proposta.py`: testes automatizados (`python -m unittest -v`).

Validação realizada: nove testes automatizados, incluindo colagem de valores brasileiros, cálculos, importação, validações e geração do PDF para os dez códigos (acomodações individuais e duplas). Interface Streamlit não executada neste ambiente; código compilado sintaticamente.
