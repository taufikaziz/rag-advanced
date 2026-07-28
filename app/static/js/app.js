const API_BASE = '/api/v1';

function setStatus(text, type) {
    document.getElementById('statusText').textContent = text;
    const dot = document.getElementById('statusDot');
    dot.classList.remove('busy', 'error');
    if (type === 'busy') dot.classList.add('busy');
    if (type === 'error') dot.classList.add('error');
}

function resetNodes() {
    document.querySelectorAll('.pipeline-node').forEach(n => {
        n.classList.remove('active', 'done', 'error');
    });
}

function setNodeState(id, state) {
    const node = document.getElementById('node-' + id);
    if (!node) return;
    node.classList.remove('active', 'done', 'error');
    if (state) node.classList.add(state);
}

function showLoading(stage) {
    document.getElementById('loadingOverlay').classList.add('visible');
    document.getElementById('loadingStage').textContent = stage || '';
}

function hideLoading() {
    document.getElementById('loadingOverlay').classList.remove('visible');
}

function sleep(ms) {
    return new Promise(function(r) { setTimeout(r, ms); });
}

async function processQuery() {
    const query = document.getElementById('queryInput').value.trim();
    if (!query) return;

    const btn = document.getElementById('submitBtn');
    btn.disabled = true;
    document.getElementById('resultsSection').style.display = 'none';
    resetNodes();
    setStatus('Processing...', 'busy');
    showLoading('Memulai pipeline...');

    setNodeState('user', 'active');
    await sleep(400);
    setNodeState('user', 'done');
    setNodeState('api', 'active');
    await sleep(300);
    setNodeState('api', 'done');

    try {
        const enableRewrite = document.getElementById('toggleRewrite').checked;
        const enableHyDE = document.getElementById('toggleHyDE').checked;
        const enableDecompose = document.getElementById('toggleDecompose').checked;
        const enableEval = document.getElementById('toggleEval').checked;

        showLoading('Query Processing...');
        setNodeState('rewrite', 'active');
        setNodeState('hyde', 'active');
        setNodeState('decompose', 'active');
        await sleep(600);
        setNodeState('rewrite', 'done');
        setNodeState('hyde', 'done');
        setNodeState('decompose', 'done');

        showLoading('Hybrid Retrieval...');
        setNodeState('retrieval', 'active');
        await sleep(600);
        setNodeState('retrieval', 'done');

        showLoading('Cross-Encoder Reranking...');
        setNodeState('rerank', 'active');
        await sleep(500);
        setNodeState('rerank', 'done');

        showLoading('Preparing context...');
        setNodeState('topk', 'active');
        await sleep(300);
        setNodeState('topk', 'done');

        showLoading('LLM Generation...');
        setNodeState('llm', 'active');
        await sleep(400);

        const payload = {
            query: query,
            top_k: 5,
            enable_rewrite: enableRewrite,
            enable_hyde: enableHyDE,
            enable_decompose: enableDecompose,
            enable_evaluation: enableEval
        };

        const response = await fetch(API_BASE + '/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('HTTP ' + response.status + ': ' + (await response.text()));
        }

        const data = await response.json();

        setNodeState('llm', 'done');
        setNodeState('answer', 'active');
        await sleep(300);
        setNodeState('answer', 'done');

        if (enableEval) {
            setNodeState('eval', 'active');
            await sleep(200);
            setNodeState('eval', 'done');
        }
        setNodeState('obs', 'done');

        hideLoading();
        setStatus('Ready', '');
        btn.disabled = false;

        displayResults(data);

    } catch (err) {
        hideLoading();
        setStatus('Error', 'error');
        btn.disabled = false;
        setNodeState('api', 'error');
        document.getElementById('resultsSection').style.display = 'block';
        document.getElementById('answerContent').innerHTML = '<span style="color:#ef4444">Pipeline Error: ' + err.message + '</span>';
    }
}

function displayResults(data) {
    document.getElementById('resultsSection').style.display = 'block';

    document.getElementById('answerContent').textContent = data.answer || 'No answer generated.';

    const qp = data.query_processing;
    const qpDiv = document.getElementById('qpContent');
    if (qp) {
        var html = '';
        html += '<div class="qp-item"><div class="qp-label">Original Query</div><div class="qp-value">' + escHtml(qp.original_query) + '</div></div>';
        if (qp.rewritten_query) {
            html += '<div class="qp-item"><div class="qp-label">Rewritten Query</div><div class="qp-value">' + escHtml(qp.rewritten_query) + '</div></div>';
        }
        if (qp.hyde_document) {
            html += '<div class="qp-item"><div class="qp-label">HyDE Document</div><div class="qp-value">' + escHtml(qp.hyde_document) + '</div></div>';
        }
        if (qp.sub_queries && qp.sub_queries.length > 0) {
            html += '<div class="qp-item"><div class="qp-label">Sub-Queries</div><div class="qp-value">';
            for (var si = 0; si < qp.sub_queries.length; si++) {
                html += '- ' + escHtml(qp.sub_queries[si]) + '<br>';
            }
            html += '</div></div>';
        }
        qpDiv.innerHTML = html || '<span class="no-data">No query processing data</span>';
    } else {
        qpDiv.innerHTML = '<span class="no-data">Query processing disabled</span>';
    }

    const docs = data.documents;
    const docsDiv = document.getElementById('docsContent');
    if (docs && docs.length > 0) {
        var html2 = '';
        for (var di = 0; di < docs.length; di++) {
            var d = docs[di];
            var mc = 'label-' + (d.retrieval_method || 'hybrid');
            html2 += '<div class="doc-item">' +
                '<div class="doc-header">' +
                '<span class="doc-rank">#' + d.rank + '</span>' +
                '<span><span class="doc-label ' + mc + '">' + (d.retrieval_method || 'hybrid') + '</span>' +
                ' <span class="doc-score">score: ' + d.score + '</span></span>' +
                '</div>' +
                '<div class="doc-source">' + escHtml(d.source || 'Unknown') + '</div>' +
                '<div class="doc-content">' + escHtml(d.content) + '</div>' +
                '</div>';
        }
        docsDiv.innerHTML = html2;
    } else {
        docsDiv.innerHTML = '<span class="no-data">No documents retrieved</span>';
    }

    const ev = data.evaluation;
    const evalDiv = document.getElementById('evalContent');
    if (ev) {
        var evHtml = '<div class="eval-grid">';
        var metrics = [
            { key: 'faithfulness', label: 'Faithfulness' },
            { key: 'relevancy', label: 'Relevancy' },
            { key: 'precision', label: 'Precision' },
            { key: 'recall', label: 'Recall' },
            { key: 'mrr', label: 'MRR' },
            { key: 'ndcg', label: 'nDCG' }
        ];
        for (var mi = 0; mi < metrics.length; mi++) {
            var m = metrics[mi];
            var val = ev[m.key];
            if (val !== null && val !== undefined) {
                var cls = val >= 0.8 ? 'eval-good' : (val >= 0.5 ? 'eval-warn' : 'eval-bad');
                evHtml += '<div class="eval-item"><div class="eval-value ' + cls + '">' + (val * 100).toFixed(1) + '%</div><div class="eval-label">' + m.label + '</div></div>';
            }
        }
        evHtml += '</div>';
        evalDiv.innerHTML = evHtml;
    } else {
        evalDiv.innerHTML = '<span class="no-data">No evaluation data</span>';
    }

    const tr = data.trace;
    const traceDiv = document.getElementById('traceContent');
    if (tr) {
        var tHtml = '<div class="trace-grid">';
        tHtml += '<div class="trace-item"><div class="trace-value">' + tr.latency_ms + ' ms</div><div class="trace-label">Total Latency</div></div>';
        tHtml += '<div class="trace-item"><div class="trace-value">' + tr.llm_tokens + '</div><div class="trace-label">LLM Tokens</div></div>';
        tHtml += '<div class="trace-item"><div class="trace-value">$' + (tr.llm_cost || 0).toFixed(5) + '</div><div class="trace-label">LLM Cost</div></div>';
        tHtml += '<div class="trace-item"><div class="trace-value">' + (tr.query_processing_latency_ms || 0) + ' ms</div><div class="trace-label">Query Proc</div></div>';
        tHtml += '<div class="trace-item"><div class="trace-value">' + (tr.retrieval_latency_ms || 0) + ' ms</div><div class="trace-label">Retrieval</div></div>';
        tHtml += '<div class="trace-item"><div class="trace-value">' + (tr.reranking_latency_ms || 0) + ' ms</div><div class="trace-label">Reranking</div></div>';
        tHtml += '</div>';
        traceDiv.innerHTML = tHtml;
    } else {
        traceDiv.innerHTML = '<span class="no-data">No trace data</span>';
    }
}

function escHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ====== Document Upload ======

async function loadDocuments() {
    try {
        const res = await fetch(API_BASE + '/documents');
        if (!res.ok) return;
        const data = await res.json();
        renderDocList(data.documents || []);
    } catch (e) {}
}

function renderDocList(docs) {
    var container = document.getElementById('docList');
    if (!container) return;
    if (docs.length === 0) {
        container.innerHTML = '<p class="no-data" style="text-align:center;padding:12px">No documents uploaded yet</p>';
        return;
    }
    var html = '';
    for (var i = 0; i < docs.length; i++) {
        var d = docs[i];
        var size = d.size > 1000 ? (d.size / 1000).toFixed(1) + ' KB' : d.size + ' B';
        html += '<div class="doc-item-upload" data-id="' + d.id + '">' +
            '<div class="doc-info">' +
            '<span class="doc-icon">&#128196;</span>' +
            '<div><div class="doc-name">' + escHtml(d.source) + '</div>' +
            '<div class="doc-meta">' + size + '</div></div></div>' +
            '<button class="doc-delete" onclick="deleteDoc(\'' + d.id + '\')">Delete</button></div>';
    }
    container.innerHTML = html;
}

async function deleteDoc(docId) {
    try {
        await fetch(API_BASE + '/documents/' + docId, { method: 'DELETE' });
        loadDocuments();
    } catch (e) {}
}

function setupUpload() {
    var dropzone = document.getElementById('dropzone');
    var fileInput = document.getElementById('fileInput');
    var uploadBtn = document.getElementById('uploadBtn');
    if (!dropzone || !fileInput) {
        console.warn('Upload elements not found');
        return;
    }

    dropzone.addEventListener('click', function(e) {
        if (e.target.tagName !== 'BUTTON') {
            fileInput.click();
        }
    });
    if (uploadBtn) {
        uploadBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            fileInput.click();
        });
    }

    dropzone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropzone.classList.add('drag-over');
    });
    dropzone.addEventListener('dragleave', function() {
        dropzone.classList.remove('drag-over');
    });
    dropzone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropzone.classList.remove('drag-over');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFiles(e.dataTransfer.files);
        }
    });

    fileInput.addEventListener('change', function() {
        if (fileInput.files && fileInput.files.length > 0) {
            handleFiles(fileInput.files);
            fileInput.value = '';
        }
    });
}

async function handleFiles(files) {
    var progress = document.getElementById('uploadProgress');
    var fill = document.getElementById('progressFill');
    var status = document.getElementById('uploadStatus');
    if (!progress || !fill || !status) return;
    progress.style.display = 'block';

    for (var i = 0; i < files.length; i++) {
        var file = files[i];
        status.textContent = 'Reading ' + file.name + '...';
        fill.style.width = ((i / files.length) * 100) + '%';

        try {
            var content = await new Promise(function(resolve, reject) {
                var reader = new FileReader();
                reader.onload = function() {
                    var result = reader.result;
                    var b64 = result.split(',')[1];
                    resolve(b64);
                };
                reader.onerror = reject;
                reader.readAsDataURL(file);
            });

            var res = await fetch(API_BASE + '/documents/upload', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: file.name, content: content })
            });
            if (!res.ok) {
                var errData = await res.json();
                status.textContent = 'Error: ' + (errData.detail || 'Upload failed');
                continue;
            }
            var data = await res.json();
            status.textContent = file.name + ' uploaded (' + data.chunks + ' chunks)';
        } catch (e) {
            status.textContent = 'Error uploading ' + file.name;
        }
    }
    fill.style.width = '100%';
    loadDocuments();
    setTimeout(function() { progress.style.display = 'none'; }, 3000);
}

// ====== Init ======
document.addEventListener('DOMContentLoaded', function() {
    setStatus('Ready', '');

    var submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', processQuery);
    }

    var queryInput = document.getElementById('queryInput');
    if (queryInput) {
        queryInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') processQuery();
        });
    }

    loadDocuments();
    setupUpload();
});
