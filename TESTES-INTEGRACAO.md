# Testes de integração com apoio de GenAI

## Cenário considerado

O sistema monitora movimentações bancárias. Nesta atividade, o recorte é a jornada de sincronização de uma conta: o frontend solicita a operação à API; a API valida a conta e agenda o processamento; o worker consulta o provedor bancário, persiste movimentações e ocorrências e pode solicitar o envio de uma notificação.

Os testes devem verificar a comunicação real entre componentes do sistema. Provedor bancário e serviço de notificação devem ser substituídos por servidores fake ou ambientes sandbox controlados, nunca por contas ou dados bancários reais. Os dados abaixo são sintéticos.

## Premissas explícitas

O discovery anterior ainda não definiu contratos completos. Para tornar os exemplos verificáveis, esta atividade assume provisoriamente:

- `POST /contas/{id}/sincronizar` responde `202 Accepted` com um `jobId` quando aceita a solicitação;
- uma consulta de status do job retorna `queued`, `processing`, `succeeded` ou `failed`;
- o worker evita duplicar movimentações quando o provedor retorna novamente o mesmo identificador externo;
- um evento de movimentação pode disparar uma regra e gerar no máximo uma ocorrência por movimentação e regra;
- falhas externas transitórias podem ser tentadas novamente, mas seus limites e tempos ainda precisam ser decididos.

Essas são premissas de teste, não requisitos confirmados. Devem ser substituídas pelo contrato aprovado antes da implementação definitiva.

## Prompt 1: gerar cenários de integração por jornada

**Tipo:** prompt de geração de cenários funcionais com foco em comunicação entre componentes.

**Prompt utilizado:**

```text
Atue como QA sênior. Gere casos de teste de integração para a jornada de sincronização descrita abaixo. Foque nas interações entre API, worker, provedor bancário fake, banco de dados e serviço de notificação fake; não gere testes unitários de funções isoladas.

Jornada: POST /contas/{id}/sincronizar agenda um job; o worker consulta movimentações; persiste os dados; aplica regras de monitoramento; e solicita notificação somente se uma regra for disparada.

Premissas provisórias: a API responde 202 e jobId; jobs percorrem queued, processing e succeeded/failed; movimentações repetidas do mesmo identificador externo não devem ser duplicadas; uma ocorrência por movimentação e regra; dados sempre sintéticos.

Retorne uma tabela com ID, objetivo, preparação, ação, verificações em cada componente e resultado esperado. Inclua sucesso, ausência de alerta, repetição/idempotência e conta inválida. Não invente códigos HTTP ou regras além das premissas; sinalize lacunas como perguntas.
```

**Casos de integração registrados após revisão:**

| ID | Objetivo | Preparação e ação | Verificações | Resultado esperado |
|---|---|---|---|---|
| INT-01 | Sincronizar e alertar em uma movimentação relevante | Configurar conta sintética ativa, regra de valor acima de 500 e provedor fake com crédito de 750; chamar o endpoint | API retorna `202` e `jobId`; job termina `succeeded`; movimento e ocorrência estão persistidos; notificador recebe uma solicitação | Uma movimentação e uma ocorrência; uma solicitação de notificação |
| INT-02 | Sincronizar sem disparar regra | Configurar regra de valor acima de 500 e movimento de débito de 40; chamar o endpoint | Job termina `succeeded`; movimento persiste; nenhuma ocorrência nem envio ao notificador | Sincronização concluída sem alerta |
| INT-03 | Impedir duplicação ao receber novamente a mesma movimentação | Fazer o provedor fake retornar o mesmo identificador externo em duas sincronizações | Consultar registros e ocorrências após ambas as execuções | Uma movimentação persistida; no máximo uma ocorrência por regra; comportamento de notificação de repetição precisa seguir política definida |
| INT-04 | Rejeitar solicitação para conta inexistente | Chamar o endpoint com identificador de conta inexistente | Verificar resposta da API e confirmar que não houve job, consulta ao provedor ou escrita de movimentação | Solicitação rejeitada; status HTTP e formato de erro devem ser definidos no contrato |

## Prompt 2: explorar falhas e contratos entre componentes

**Tipo:** prompt de geração de cenários negativos e de consistência/resiliência.

**Prompt utilizado:**

```text
Atue como engenheiro de qualidade especializado em integração e resiliência. Partindo da jornada API -> worker -> provedor bancário -> banco de dados -> notificador, gere casos negativos de integração para timeout/indisponibilidade do provedor, resposta inválida do provedor, falha ao persistir, falha no notificador e repetição de job.

Para cada caso, informe: ponto de injeção da falha, configuração do stub, ação, observações necessárias em todos os componentes, risco de duplicação/perda e resultado esperado. Use somente contas e eventos sintéticos. Não assuma política de retry, dead-letter, timeout, compensação ou status HTTP que não foi especificada: marque cada uma como decisão pendente e proponha opções sem escolher por conta do time.

Retorne uma tabela priorizada. Separe comportamento já dedutível daquilo que depende de decisão arquitetural.
```

**Casos de integração registrados após revisão:**

| ID | Falha injetada | Ação e verificações | Resultado esperado / decisão pendente |
|---|---|---|---|
| INT-05 | Timeout do provedor fake | Iniciar sincronização; verificar estado do job, chamadas subsequentes ao provedor e persistência | Falha não deve ser apresentada como sucesso. Número de tentativas, backoff, timeout final e estado terminal precisam ser definidos |
| INT-06 | Resposta inválida do provedor | Fazer o stub retornar payload sem identificador externo ou com campo obrigatório inválido | Dados inválidos não devem virar movimentações válidas; política de rejeição do lote versus item e registro de erro precisam ser definidos |
| INT-07 | Banco indisponível durante persistência | Simular falha de conexão depois de receber a resposta do provedor | Job não deve terminar como sucesso antes da persistência; recuperação e prevenção de perda/reprocessamento precisam ser especificadas |
| INT-08 | Notificador indisponível | Aceitar e persistir movimentação/ocorrência, mas responder erro no stub do notificador | A movimentação não deve ser perdida por falha de notificação; retry, fila de saída, estado da entrega e possibilidade de duplicação precisam ser decididos |
| INT-09 | Job repetido ou entrega duplicada | Enfileirar duas vezes a mesma solicitação/job com o mesmo identificador de idempotência (a definir) | Não duplicar movimentação nem ocorrência; regra para notificações repetidas e armazenamento da chave de idempotência precisam ser formalizados |

## Reflexão para o fórum

### Como cada tipo de prompt influenciou os casos

O prompt de jornada funcional gerou uma cobertura mais direta do caminho esperado e ajudou a diversificar os cenários entre sucesso, ausência de alerta, repetição de dados e conta inexistente. Pedir preparação, ação e verificações por componente tornou os resultados mais executáveis do que uma solicitação genérica por “testes”.

O prompt de falhas ampliou a cobertura para indisponibilidade e inconsistência entre componentes, especialmente nos limites entre provedor, persistência e notificação. Ao pedir que o modelo separasse comportamento dedutível de decisões pendentes, os casos ficaram menos propensos a apresentar escolhas de resiliência inventadas como fatos.

### Ajustes necessários nos prompts

- Informar explicitamente que o escopo é integração, excluindo testes unitários;
- nomear os componentes e o fluxo para que cada caso valide mais de uma fronteira;
- exigir dados sintéticos e stubs/sandbox para não usar dados bancários reais;
- pedir preparação, ação, verificações e resultado esperado para tornar os casos executáveis;
- incluir premissas provisórias do contrato e orientar a LLM a sinalizar lacunas em vez de inventar status, retries ou garantias;
- revisar manualmente termos ambíguos como “idempotência” e “sucesso” antes de transformar os exemplos em automação.

## Limitações e próximos passos

Os casos são uma proposta de discovery e não substituem um contrato aprovado nem a execução em uma aplicação existente. Para automatizá-los, ainda são necessários: OpenAPI, esquema dos eventos do provedor, estados e transições do job, política de retries e idempotência, regras de alerta, garantias transacionais, estratégia de fila e critérios para reprocessamento. Os testes devem usar banco isolado por execução e limpar seus dados ao final.

## Texto pronto para a postagem

Use este resumo no fórum junto com o link do repositório:

> Escolhi a jornada de sincronização de movimentações do sistema de monitoramento bancário. Usei dois tipos de prompt: um para gerar cenários funcionais cobrindo a integração entre API, worker, provedor e notificador; outro para explorar falhas, contratos e consistência entre componentes. O primeiro trouxe casos de sucesso, ausência de alerta, duplicidade e conta inválida. O segundo ampliou a cobertura para timeout, payload inválido e indisponibilidade do banco e do notificador.
>
> A especificação de componentes e o pedido de preparação, ação e verificações deixaram os casos mais úteis. Ajustei os prompts para exigir dados sintéticos, separar teste de integração de teste unitário e pedir que lacunas fossem marcadas em vez de preenchidas por suposição. O principal limite é que ainda faltam decisões formais sobre status HTTP, retries, idempotência e recuperação de falhas; por isso, registrei essas premissas como provisórias no repositório.