// static-src/copy.ts
import { byIdT } from "./dom.js";

async function copyText(text: string): Promise<boolean> {
  if (!navigator.clipboard?.writeText) return false;

  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (e) {
    console.error("navigator.clipboard.writeText failed", e);
    return false;
  }
}

function setupCopyButton(): void {
  const btn = byIdT<HTMLButtonElement>("copyBtn");
  const textarea = byIdT<HTMLTextAreaElement>("reportText");
  if (!btn || !textarea) return;

  btn.addEventListener("click", async () => {
    const ok = await copyText(textarea.value ?? "");
    if (ok) {
      alert("診断文をクリップボードにコピーしました。");
    } else {
      alert("コピーに失敗しました。テキストを選択して Cmd+C でコピーしてください。");
      textarea.focus();
      textarea.select();
    }
  });
}

document.addEventListener("DOMContentLoaded", setupCopyButton);

export const __copy_ts_module = true;
