// Fixture: função alfa do exemplo.
export function alfa(entrada: string): string {
  const limpa = entrada.trim();
  if (limpa.length === 0) {
    return "";
  }
  return `alfa:${limpa}`;
}

export const VERSAO = 1;
export const NOME = "alfa";
