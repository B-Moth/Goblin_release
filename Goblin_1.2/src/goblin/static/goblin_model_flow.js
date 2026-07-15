(() => {
  // GoblinModelFlow — small client-side helper to manage checks and
  // background pulls for local Ollama models used by the transcription
  // editor. The module exposes a simple `init` and `prepareAction`
  // function so the existing preview/save flows can ask the module to
  // ensure the requested model is available before continuing.
  const state = {
    addMessage: null,
    getState: null,
    onRetryPreview: null,
    onRetrySave: null,
  };

  function setStatus(text, kind) {
    const editorStatus = document.getElementById('editor-local-model-status');
    const viewerStatus = document.getElementById('viewer-local-model-status');
    [editorStatus, viewerStatus].forEach((el) => {
      if (!el) return;
      el.textContent = text;
      el.dataset.kind = kind || '';
    });
  }

  function getProviderAndModel() {
    const current = state.getState ? state.getState() : {};
    const providerSelect = document.getElementById('editor-provider-select');
    const localModelSelect = document.getElementById('editor-local-model-select');
    return {
      provider: providerSelect?.value || current.editorProvider || 'local',
      localModel: localModelSelect?.value || current.editorLocalModel || '',
    };
  }

  async function refreshStatus() {
    const { provider, localModel } = getProviderAndModel();
    if (provider !== 'local') {
      setStatus('État : mode en ligne', 'info');
      return;
    }
    try {
      const response = await fetch('/ollama/check-model?model=' + encodeURIComponent(localModel));
      const data = await response.json().catch(() => ({}));
      // Map backend messages to user-visible status badges.
      if (data.message === 'ollama_not_installed') {
        setStatus('État : Ollama non installé', 'error');
      } else if (data.message === 'pulling') {
        setStatus('État : téléchargement en cours', 'warning');
      } else if (data.present) {
        setStatus('État : modèle disponible', 'success');
      } else {
        setStatus('État : modèle à télécharger', 'warning');
      }
    } catch (err) {
      setStatus('État : vérification indisponible', 'warning');
    }
  }

  async function startPullAndWait(localModel, onDone) {
    const start = await fetch('/ollama/pull-model', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({model: localModel}),
    }).then((r) => r.json().catch(() => ({})));
    if (!start.ok) {
      // Backend refused the pull (e.g. Ollama not installed). Surface
      // the error to the user and abort the action.
      state.addMessage?.('Impossible de démarrer le téléchargement du modèle local: ' + (start.error || 'erreur'), 'error');
      return false;
    }

    // Show the progress modal
    showModelDownloadProgress(localModel);
    setStatus('État : téléchargement en cours', 'warning');

    // Poll job status until the server reports the pull is complete or failed.
    const poll = setInterval(async () => {
      const s = await fetch('/ollama/pull-status?model=' + encodeURIComponent(localModel))
        .then((r) => r.json().catch(() => ({})));
      
      if (s && s.progress) {
        updateModelDownloadProgress(s.progress);
      }
      
      if (s && s.status === 'done') {
        clearInterval(poll);
        setStatus('État : modèle disponible', 'success');
        closeModelDownloadModal();
        state.addMessage?.('Modèle téléchargé — prêt à reprendre.', 'info');
        onDone?.();
      } else if (s && s.status === 'failed') {
        clearInterval(poll);
        setStatus('État : échec du téléchargement', 'error');
        updateModelDownloadProgress({ status: 'error', percentage: 0 });
        showModelDownloadError(s.progress?.error || 'Erreur inconnue lors du téléchargement');
      }
    }, 1000);
    return false;
  }

  function showModelDownloadProgress(modelName) {
    const modal = document.getElementById('model-download-modal');
    const title = document.getElementById('model-download-name');
    if (!modal || !title) return;
    
    title.textContent = `Téléchargement de "${modelName}"...`;
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    
    // Disable close button during download
    const cancelBtn = document.getElementById('model-download-cancel');
    if (cancelBtn) {
      cancelBtn.textContent = 'Attendre la fin…';
      cancelBtn.disabled = true;
    }
  }

  function updateModelDownloadProgress(progress) {
    const bar = document.getElementById('model-download-progress-bar');
    const pct = document.getElementById('model-download-percentage');
    const speed = document.getElementById('model-download-speed');
    const downloaded = document.getElementById('model-download-downloaded');
    const total = document.getElementById('model-download-total');
    
    if (!bar || !pct) return;
    
    const percentage = progress.percentage || 0;
    bar.style.width = percentage + '%';
    bar.textContent = percentage + '%';
    pct.textContent = percentage + '%';
    speed.textContent = progress.speed || '—';
    downloaded.textContent = progress.downloaded || '—';
    total.textContent = progress.total || '—';
  }

  function showModelDownloadError(error) {
    const statusDiv = document.getElementById('model-download-status');
    const cancelBtn = document.getElementById('model-download-cancel');
    if (!statusDiv) return;
    
    statusDiv.textContent = 'Erreur : ' + error;
    statusDiv.style.display = 'block';
    statusDiv.style.backgroundColor = '#fee2e2';
    statusDiv.style.color = '#991b1b';
    
    if (cancelBtn) {
      cancelBtn.textContent = 'Fermer';
      cancelBtn.disabled = false;
    }
  }

  function closeModelDownloadModal() {
    const modal = document.getElementById('model-download-modal');
    const statusDiv = document.getElementById('model-download-status');
    if (!modal) return;
    
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    
    // Reset status message
    if (statusDiv) {
      statusDiv.style.display = 'none';
      statusDiv.textContent = '';
    }
    
    // Re-enable cancel button
    const cancelBtn = document.getElementById('model-download-cancel');
    if (cancelBtn) {
      cancelBtn.textContent = 'Fermer';
      cancelBtn.disabled = false;
    }
  }

  async function prepareAction(actionName) {
    const { provider, localModel } = getProviderAndModel();
    if (provider !== 'local') {
      return true;
    }

    try {
      const response = await fetch('/ollama/check-model?model=' + encodeURIComponent(localModel));
      const data = await response.json().catch(() => ({}));
      if (data.message === 'ollama_not_installed') {
        state.addMessage?.("Le runtime local (Ollama) n'est pas installé. Installez Ollama ou passez en mode en ligne.", 'error');
        return false;
      }

      // If the model is already present the caller can proceed.
      if (data.present) {
        return true;
      }

      // Special handling for Qwen 14B - ask to download or revert to 7B
      if (localModel && localModel.includes('14b')) {
        const confirmDownload = window.confirm(
          'Le modèle Qwen 14B n\'est pas installé.\n\n' +
          'Voulez-vous le télécharger maintenant ?\n\n' +
          '(~4.7 GB, cela peut prendre plusieurs minutes)\n\n' +
          'Oui : Démarrer le téléchargement\n' +
          'Non : Revenir à Qwen 7B'
        );
        
        if (!confirmDownload) {
          // Revert to Qwen 7B
          const localModelSelect = document.getElementById('editor-local-model-select');
          if (localModelSelect) {
            localModelSelect.value = 'qwen2.5:7b-instruct';
          }
          state.addMessage?.('Modèle changé vers Qwen 7B.', 'info');
          return false;
        }

        // Start the download with progress modal
        await startPullAndWait(localModel, state.onRetryPreview);
        return false;
      }

      // For a save action we prefer that the user runs a preview first
      // which triggers the model download; this avoids long-blocking
      // saves where the user may be surprised by a large download.
      if (actionName === 'save') {
        state.addMessage?.("Le modèle local n'est pas encore prêt. Lancez un Aperçu pour déclencher le téléchargement, puis réessayez l'enregistrement.", 'warning');
        return false;
      }

      const confirmPull = window.confirm('Le modèle local sélectionné n\'est pas présent et sera téléchargé (plusieurs centaines de MB). Voulez-vous continuer ?');
      if (!confirmPull) {
        return false;
      }

      // Start the background pull and wait until it's finished before
      // allowing the preview flow to continue. The UI behaviour is to
      // retry the preview transparently via `state.onRetryPreview` when
      // the pull completes.
      await startPullAndWait(localModel, state.onRetryPreview);
      return false;
    } catch (err) {
      console.warn('Model check failed:', err);
      return true;
    }
  }

  function bind() {
    const providerSelect = document.getElementById('editor-provider-select');
    const localModelSelect = document.getElementById('editor-local-model-select');
    if (providerSelect) {
      providerSelect.addEventListener('change', refreshStatus);
    }
    if (localModelSelect) {
      localModelSelect.addEventListener('change', refreshStatus);
    }
    refreshStatus();
  }

  window.GoblinModelFlow = {
    init(options) {
      state.addMessage = options.addMessage || null;
      state.getState = options.getState || null;
      state.onRetryPreview = options.onRetryPreview || null;
      state.onRetrySave = options.onRetrySave || null;
    },
    bind,
    refreshStatus,
    prepareAction,
    setStatus,
  };

  // Export closeModelDownloadModal to global scope for onclick handlers
  window.closeModelDownloadModal = closeModelDownloadModal;
})();
