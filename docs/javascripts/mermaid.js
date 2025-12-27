document.addEventListener("DOMContentLoaded", function() {
    import("<https://unpkg.com/mermaid@10.9.0/dist/mermaid.esm.min.mjs").then(m> => {
        m.default.initialize({
            startOnLoad: true,
            theme: document.body.getAttribute("data-md-color-scheme") === "slate" ? "dark" : "default"
        });
    });
});
