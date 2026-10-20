//componentes react que criam a interfade, como botoes, votacaoes e resultados

import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { api, voterToken } from "./api";
import "./style.css";

const statusLabels = { draft: "Rascunho", open: "Aberta", closed: "Fechada" };

// Cada cartão tem os seus resultados e um botão de atualização manual.
function Results({ pollId, host }) {
  const [results, setResults] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function refresh() {
    setLoading(true);
    setError("");
    try {
      setResults(
        await api(`${host ? "host" : "public"}/polls/${pollId}/results/`),
      );
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    refresh();
  }, [pollId, host]);
  return (
    <section className="results" aria-label="Resultados">
      <div className="row">
        <h3>Resultados</h3>
        <button className="subtle" onClick={refresh} disabled={loading}>
          {loading ? "A atualizar…" : "Atualizar resultados"}
        </button>
      </div>
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {results && (
        <>
          <p className="muted">
            {results.total}{" "}
            {results.total === 1 ? "voto registado" : "votos registados"}
          </p>
          {results.options.map((option) => (
            <div className="result" key={option.id}>
              <div className="row">
                <span>{option.text}</span>
                <strong>
                  {option.count} · {option.percentage.toLocaleString("pt-PT")}%
                </strong>
              </div>
              <div
                className="bar"
                role="img"
                aria-label={`${option.text}: ${option.count} votos, ${option.percentage}%`}
              >
                <div style={{ width: `${option.percentage}%` }} />
              </div>
            </div>
          ))}
        </>
      )}
    </section>
  );
}

// O mesmo cartão apresenta ações diferentes ao público e ao anfitrião.
function PollCard({ poll, host, onChange }) {
  const [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [confirmation, setConfirmation] = useState("");
  async function submitVote(event) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const data = await api(`public/polls/${poll.id}/vote/`, "POST", {
        option_id: Number(selected),
        token: voterToken(),
      });
      setConfirmation(data.detail);
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }
  async function changeStatus() {
    setBusy(true);
    setError("");
    try {
      await api(`host/polls/${poll.id}/status/`, "PATCH", {
        status: poll.status === "draft" ? "open" : "closed",
      });
      await onChange();
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <article className="card">
      <div className="row">
        <span className={`badge ${poll.status}`}>
          {statusLabels[poll.status]}
        </span>
        <span className="muted">#{String(poll.id).padStart(2, "0")}</span>
      </div>
      <h2>{poll.question}</h2>
      {host ? (
        <>
          <ul className="option-list">
            {poll.options.map((option) => (
              <li key={option.id}>{option.text}</li>
            ))}
          </ul>
          {poll.status !== "closed" && (
            <button onClick={changeStatus} disabled={busy}>
              {busy
                ? "A guardar…"
                : poll.status === "draft"
                  ? "Abrir votação"
                  : "Fechar votação"}
            </button>
          )}
        </>
      ) : poll.status === "open" ? (
        <>
          {confirmation ? (
            <p className="success" role="status">
              {confirmation}
            </p>
          ) : (
            <form onSubmit={submitVote}>
              <fieldset disabled={busy}>
                <legend>Escolha uma opção</legend>
                {poll.options.map((option) => (
                  <label
                    className={`choice ${selected === String(option.id) ? "selected" : ""}`}
                    key={option.id}
                  >
                    <input
                      type="radio"
                      name={`poll-${poll.id}`}
                      value={option.id}
                      checked={selected === String(option.id)}
                      onChange={(event) => setSelected(event.target.value)}
                      required
                    />
                    {option.text}
                  </label>
                ))}
              </fieldset>
              <button disabled={busy || !selected}>
                {busy ? "A registar…" : "Registar voto"}
              </button>
            </form>
          )}
          <p className="muted note">
            Os resultados serão publicados quando a votação fechar.
          </p>
        </>
      ) : (
        <p className="muted">
          A participação terminou. Consulte os resultados abaixo.
        </p>
      )}
      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
      {(host || poll.status === "closed") && (
        <Results pollId={poll.id} host={host} />
      )}
    </article>
  );
}

// A validação no formulário ajuda o utilizador; o backend volta a validar tudo.
function CreatePoll({ onCreated }) {
  const [question, setQuestion] = useState("");
  const [options, setOptions] = useState(["", ""]);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");
    if (!question.trim() || options.some((option) => !option.trim())) {
      setError("Preencha a pergunta e todas as opções.");
      return;
    }
    if (
      new Set(options.map((option) => option.trim().toLocaleLowerCase("pt-PT")))
        .size !== options.length
    ) {
      setError("As opções não podem estar repetidas.");
      return;
    }
    setBusy(true);
    try {
      await api("host/polls/", "POST", { question, options });
      setQuestion("");
      setOptions(["", ""]);
      setSuccess("Votação criada em rascunho. Abra-a quando estiver pronta.");
      await onCreated();
    } catch (error) {
      setError(error.message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="card create">
      <span className="eyebrow">UMA NOVA CONVERSA</span>
      <h2>Criar votação</h2>
      <form onSubmit={submit}>
        <fieldset disabled={busy}>
          <legend className="sr-only">Dados da nova votação</legend>
          <label htmlFor="question">Pergunta</label>
          <input
            id="question"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            maxLength={255}
            required
            placeholder="O que queremos decidir hoje?"
          />
          <div className="row">
            <h3>Opções de resposta</h3>
            <span className="muted">{options.length}/5</span>
          </div>
          {options.map((option, index) => (
            <div className="option-input" key={index}>
              <label className="sr-only" htmlFor={`option-${index}`}>
                Opção {index + 1}
              </label>
              <input
                id={`option-${index}`}
                value={option}
                onChange={(event) =>
                  setOptions(
                    options.map((text, i) =>
                      i === index ? event.target.value : text,
                    ),
                  )
                }
                maxLength={255}
                required
                placeholder={`Opção ${index + 1}`}
              />
              {options.length > 2 && (
                <button
                  type="button"
                  className="subtle"
                  aria-label={`Remover opção ${index + 1}`}
                  onClick={() =>
                    setOptions(options.filter((_, i) => i !== index))
                  }
                >
                  Remover
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            className="subtle add"
            disabled={options.length >= 5}
            onClick={() => setOptions([...options, ""])}
          >
            + Adicionar opção
          </button>
        </fieldset>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        {success && (
          <p className="success" role="status">
            {success}
          </p>
        )}
        <button disabled={busy}>
          {busy ? "A criar…" : "Guardar rascunho"}
        </button>
      </form>
    </section>
  );
}

// A lista é pedida ao endpoint da área escolhida.
function Dashboard({ host }) {
  const [polls, setPolls] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  async function refresh() {
    setLoading(true);
    setError("");
    try {
      setPolls(await api(`${host ? "host" : "public"}/polls/`));
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    refresh();
  }, [host]);
  return (
    <>
      <section className="intro">
        <span className="eyebrow">
          {host ? "PAINEL DO ANFITRIÃO" : "ESPAÇO DO PÚBLICO"}
        </span>
        <h1>{host ? "Dê voz às suas ideias." : "A sua opinião conta."}</h1>
        <p>
          {host
            ? "Crie perguntas, abra a participação e acompanhe cada resposta."
            : "Escolha uma votação, participe e descubra o que pensamos em conjunto."}
        </p>
      </section>
      {host && (
        <p className="notice">
          Painel sem autenticação, conforme o desafio. Qualquer pessoa com
          acesso à aplicação pode gerir as votações.
        </p>
      )}
      <div className={host ? "host-layout" : ""}>
        {host && <CreatePoll onCreated={refresh} />}
        <section className="polls">
          <div className="row list-heading">
            <h2>{host ? "As votações" : "Votações disponíveis"}</h2>
            <button className="subtle" onClick={refresh} disabled={loading}>
              {loading ? "A carregar…" : "Atualizar lista"}
            </button>
          </div>
          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
          {!loading && !error && polls.length === 0 && (
            <div className="card empty">
              <h3>A conversa começa aqui</h3>
              <p>
                {host
                  ? "Crie a primeira votação no formulário."
                  : "Ainda não há votações disponíveis. Volte a atualizar a lista em breve."}
              </p>
            </div>
          )}
          <div className="poll-grid">
            {polls.map((poll) => (
              <PollCard
                key={poll.id}
                poll={poll}
                host={host}
                onChange={refresh}
              />
            ))}
          </div>
        </section>
      </div>
    </>
  );
}

// O fragmento do endereço permite abrir diretamente cada área, sem um router.
function App() {
  const [host, setHost] = useState(window.location.hash === "#anfitriao");
  useEffect(() => {
    const update = () => setHost(window.location.hash === "#anfitriao");
    window.addEventListener("hashchange", update);
    return () => window.removeEventListener("hashchange", update);
  }, []);
  return (
    <>
      <header>
        <a className="brand" href="#publico">
          <span className="brand-icon">≋</span>Live Pulse
          <span className="brand-dot">●</span>
        </a>
        <nav aria-label="Área da aplicação">
          <a href="#publico" aria-current={!host ? "page" : undefined}>
            Público
          </a>
          <a href="#anfitriao" aria-current={host ? "page" : undefined}>
            Anfitrião
          </a>
        </nav>
      </header>
      <main>
        <Dashboard key={host ? "host" : "public"} host={host} />
      </main>
      <footer>
        <strong>Live Pulse</strong>
        <span>Cada voto conta. Cada opinião tem lugar.</span>
        <span>jeKnowledge · Níveis 1 e 2</span>
      </footer>
    </>
  );
}

createRoot(document.getElementById("root")).render(<App />);
