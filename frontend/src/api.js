const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api";

function errorText(value) {
  if (Array.isArray(value)) return value.map(errorText).join(" ");
  if (value && typeof value === "object") {
    return Object.entries(value)
      .map(([key, message]) => {
        const labels = {
          question: "Pergunta",
          options: "Opções",
          token: "Identificador do navegador",
          option_id: "Opção",
        };
        return key === "detail"
          ? errorText(message)
          : `${labels[key] || key}: ${errorText(message)}`;
      })
      .join(" ");
  }
  return String(value);
}

export async function api(path, method = "GET", body) {
  let response;
  try {
    response = await fetch(`${API_URL}/${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  } catch {
    throw new Error(
      "Não foi possível contactar o servidor. Confirme que o Django está em execução.",
    );
  }
  const data = await response.json().catch(() => null);
  if (!response.ok)
    throw new Error(
      data ? errorText(data) : "O servidor não conseguiu concluir o pedido.",
    );
  return data;
}

export function voterToken() {
  try {
    let token = localStorage.getItem("live-pulse-token");
    const uuid =
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!token || !uuid.test(token)) {
      token = crypto.randomUUID();
      localStorage.setItem("live-pulse-token", token);
    }
    return token;
  } catch {
    throw new Error(
      "Permita o armazenamento local no navegador para poder votar.",
    );
  }
}
