document.addEventListener("DOMContentLoaded", () => {
  const btn = document.getElementById("copyBtn");
  const textarea = document.getElementById("reportText");

  if (!btn || !textarea) return;

  btn.addEventListener("click", async () => {
    const text = textarea.value;

    // 1. Modern clipboard API (localhost is treated as secure in browsers)
    if (navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(text);
        alert("診断文をクリップボードにコピーしました。");
        return;
      } catch (e) {
        console.error("navigator.clipboard failed", e);
      }
    }

    // 2. Fallback
    textarea.focus();
    textarea.select();
    try {
      const success = document.execCommand("copy");
      if (success) {
        alert("診断文をクリップボードにコピーしました。");
      } else {
        alert("コピーに失敗しました。テキストを選択して Cmd+C でコピーしてください。");
      }
    } catch (e) {
      console.error('execCommand("copy") failed', e);
      alert("コピーに失敗しました。テキストを選択して Cmd+C でコピーしてください。");
    }
  });
});
