# Manual do Usuário — LuzAgenda

**Sistema de agendamento de visitas e ligações — Clínica Luz da Vida**  
Versão 1.0 | 2026

---

## Para quem é este manual

Este manual é destinado a dois perfis:

- **Visitantes e familiares** — pessoas que desejam agendar uma visita ou ligação para um acolhido
- **Equipe administrativa** — colaboradores que utilizam o painel de administração da clínica

---

## Parte 1 — Agendamento de Visita (acesso público)

### 1.1 Acessar o sistema

Abra o navegador no celular ou computador e acesse:

```
https://luz-agenda.onrender.com
```

Na página inicial, toque em **Agendar Visita**.

> **Dica:** você pode instalar o LuzAgenda no celular como aplicativo. Ao acessar pelo Chrome/Safari, aparecerá a opção "Adicionar à tela inicial". Isso facilita agendamentos futuros.

---

### 1.2 Leia o informativo obrigatório

Antes de prosseguir, um aviso importante será exibido sobre as regras de alimentação nas visitas. Leia com atenção e toque em **Li e entendi** para continuar.

> Visitantes podem trazer comida, lanche, refrigerante, sobremesa, doce e afins, desde que sejam consumidos durante a visita. Itens em grande quantidade que sobrem serão devolvidos ao visitante ou, em pequena quantidade, liberados ao acolhido para o mesmo dia. Não é permitido estoque de alimentos por norma da Vigilância Sanitária.

---

### 1.3 Buscar o acolhido

Digite o nome do acolhido que deseja visitar. Uma lista de sugestões aparecerá automaticamente enquanto você digita. Selecione o nome correto.

> **Atenção:** se o acolhido não aparecer, ele pode estar inativo no sistema. Entre em contato com a equipe da clínica.

---

### 1.4 Escolher data e horário

- Selecione uma data disponível (sextas, sábados e domingos)
- Dias marcados como **lotados** não podem ser selecionados
- Escolha o horário de início e a duração da visita (2, 3 ou 4 horas)

> As visitas ocorrem das **10h às 16h**. O horário de término não pode ultrapassar 16h.

**Regra de carência:** o acolhido só pode receber visitas após **30 dias** da data de entrada. Se os 30 dias caírem em dia de semana, o sistema libera o final de semana anterior (mínimo 27 dias).

---

### 1.5 Preencher dados do responsável

Informe:
- Nome completo do responsável pela visita
- Telefone (com DDD)
- Grau de parentesco ou relação com o acolhido

---

### 1.6 Adicionar acompanhantes

Adicione os demais participantes da visita:
- Nome completo
- Parentesco ou relação
- Indique se é **adulto** ou **criança**

> **Limites:**
> - Máximo de **5 adultos** por visita (o responsável conta como 1)
> - Crianças não entram no limite de adultos
> - Máximo de **2 crianças** por visita

---

### 1.7 Confirmar o agendamento

Revise as informações e toque em **Confirmar agendamento**.

Ao confirmar, você verá a tela de sucesso com:
- Resumo completo da visita
- Botão para **enviar confirmação via WhatsApp** à equipe da clínica
- Opção de **adicionar ao Google Agenda** (link ICS)

> **Importante:** salve o link "Meu Agendamento" ou deixe a página aberta. Ele usa um código único salvo no seu navegador para que você possa consultar ou cancelar depois.

---

### 1.8 O que fazer se o dia estiver lotado

Se o dia selecionado atingiu o limite de 5 visitas, o sistema exibirá um aviso e um botão para entrar em contato com a equipe via WhatsApp. A mensagem já vem pré-preenchida com o nome do acolhido e a data desejada.

---

## Parte 2 — Agendamento de Ligação (acesso público)

### 2.1 Acessar

Na página inicial, toque em **Agendar Ligação**.

---

### 2.2 Buscar o acolhido e escolher data/horário

- Digite o nome do acolhido
- Selecione uma data disponível (quartas, quintas ou sextas)
- Escolha um slot de horário disponível (slots de 20 minutos, das 10h às 18h)

> Slots em **verde** estão disponíveis. Slots em **cinza** estão completamente ocupados (ambos os celulares em uso).

**Regra de carência:** o acolhido só pode receber ligações após **15 dias** da data de entrada.

**Cota semanal:** cada acolhido tem direito a **1 agendamento de ligação por semana** (equivalente a 20 minutos). Se a cota já foi utilizada, o sistema bloqueará o agendamento.

---

### 2.3 Preencher dados do solicitante

Informe nome completo, telefone com DDD e grau de parentesco ou relação.

---

### 2.4 Confirmar e avisar via WhatsApp

Após confirmar, a tela de sucesso exibirá:
- Qual celular foi atribuído (**Cel Acolhidos 1** ou **Cel Acolhidos 2**)
- Dois botões de WhatsApp — use o botão do celular atribuído para avisar a equipe

---

## Parte 3 — Consultar ou Cancelar seu Agendamento

### 3.1 Acessar "Meu Agendamento"

Na página inicial, toque em **Meu Agendamento**.

O sistema buscará automaticamente seu agendamento salvo no navegador. Se encontrado, exibirá todos os detalhes.

> Este recurso funciona apenas no mesmo navegador e dispositivo onde o agendamento foi feito.

---

### 3.2 Cancelar

Se precisar cancelar, toque em **Cancelar agendamento** na tela de "Meu Agendamento". O cancelamento é imediato e a vaga é liberada para outros visitantes.

Após cancelar, você poderá fazer um novo agendamento.

---

## Parte 4 — Painel Administrativo (equipe da clínica)

### 4.1 Acessar

Acesse `https://luz-agenda.onrender.com/admin/login` e informe a senha administrativa.

---

### 4.2 Dashboard

O painel inicial exibe:
- Total de pacientes ativos
- Visitas agendadas para o próximo final de semana (sexta a domingo)
- Ligações agendadas por dia da semana (quarta, quinta e sexta)
- Lista dos próximos agendamentos de visita e ligação

---

### 4.3 Gerenciar Pacientes

Em **Pacientes**, você pode:
- Cadastrar novo acolhido (nome completo, data de entrada, status)
- Buscar por nome ou filtrar por status (ativo/inativo)
- Ativar ou inativar um acolhido
- Ver o total de visitas e ligações registradas para cada paciente

> Acolhidos inativos não aparecem na busca pública do agendamento.

---

### 4.4 Gerenciar Agendamentos

Em **Agendamentos**, você pode:
- Filtrar visitas ou ligações por período
- Visualizar todos os detalhes de cada agendamento
- Cancelar qualquer agendamento diretamente pelo painel

---

## Boas práticas

- Ao agendar, **verifique o nome do acolhido** antes de confirmar
- **Não compartilhe** o link de "Meu Agendamento" com outras pessoas, pois ele dá acesso ao cancelamento
- Em caso de dúvida, entre em contato com a equipe da clínica via WhatsApp antes de fazer o agendamento
- Se for instalar o app no celular, use **Chrome (Android)** ou **Safari (iPhone)** para melhor compatibilidade

---

## Contato

Em caso de problemas com o sistema ou dúvidas sobre o agendamento, entre em contato com a equipe administrativa da Clínica Luz da Vida pelo WhatsApp.
