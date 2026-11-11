/**
 * ShabdSetu — शब्दसेतु
 * Minimal vanilla JavaScript for the dictionary frontend.
 *
 * Responsibilities:
 *   - Focus the search input on page load.
 *   - Keyboard shortcut: "/" focuses the search bar.
 *
 * Search logic lives entirely on the server (search.py).
 * This file does NOT duplicate any search functionality.
 */

(function () {
    "use strict";

    // ── Focus search input on load ──
    const searchInput = document.getElementById("search-input");
    if (searchInput && !searchInput.value) {
        searchInput.focus();
    }

    // ── "/" keyboard shortcut to focus search ──
    document.addEventListener("keydown", function (e) {
        if (
            e.key === "/" &&
            document.activeElement !== searchInput &&
            !e.ctrlKey &&
            !e.metaKey &&
            !e.altKey
        ) {
            // Don't fire if user is typing in another input.
            const tag = document.activeElement?.tagName;
            if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
                return;
            }
            e.preventDefault();
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
    });
})();

