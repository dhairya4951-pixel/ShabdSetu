/**
 * ShabdSetu — Admin Dashboard JavaScript
 *
 * Handles:
 *   - Dynamic form field management (add/remove variants & meanings)
 *   - Mobile sidebar toggle
 *   - Message auto-dismiss
 *   - Double-submit prevention
 */

(function () {
    "use strict";

    // ────────────────────────────────────────────────────────────
    //  Dynamic form rows (variants & meanings)
    // ────────────────────────────────────────────────────────────

    document.addEventListener("click", function (e) {
        // ── Add row ──
        var addBtn = e.target.closest(".btn--add-row");
        if (addBtn) {
            e.preventDefault();
            var targetId    = addBtn.getAttribute("data-target");
            var fieldName   = addBtn.getAttribute("data-name");
            var placeholder = addBtn.getAttribute("data-placeholder") || "";
            var container   = document.getElementById(targetId);
            if (!container) return;

            var row = document.createElement("div");
            row.className = "dynamic-row";
            row.innerHTML =
                '<input type="text" name="' + fieldName + '" value="" ' +
                'class="form-input" placeholder="' + placeholder + '">' +
                '<button type="button" class="btn btn--icon btn--remove-row" ' +
                'aria-label="Remove">&times;</button>';

            container.appendChild(row);

            // Focus the new input.
            var newInput = row.querySelector("input");
            if (newInput) newInput.focus();
            return;
        }

        // ── Remove row ──
        var removeBtn = e.target.closest(".btn--remove-row");
        if (removeBtn) {
            e.preventDefault();
            var row = removeBtn.closest(".dynamic-row");
            var container = row ? row.parentElement : null;

            // Never remove the last row — just clear it.
            if (container && container.querySelectorAll(".dynamic-row").length <= 1) {
                var input = row.querySelector("input");
                if (input) input.value = "";
                return;
            }

            if (row) row.remove();
            return;
        }

        // ── Message dismiss ──
        var closeBtn = e.target.closest(".message-close");
        if (closeBtn) {
            var msg = closeBtn.closest(".message");
            if (msg) msg.remove();
            return;
        }
    });

    // ────────────────────────────────────────────────────────────
    //  Mobile sidebar toggle
    // ────────────────────────────────────────────────────────────

    var sidebar      = document.getElementById("sidebar");
    var openBtn      = document.getElementById("sidebar-open");
    var closeBtn     = document.getElementById("sidebar-close");

    if (openBtn && sidebar) {
        openBtn.addEventListener("click", function () {
            sidebar.classList.add("sidebar--open");
        });
    }

    if (closeBtn && sidebar) {
        closeBtn.addEventListener("click", function () {
            sidebar.classList.remove("sidebar--open");
        });
    }

    // Close sidebar when clicking outside on mobile.
    document.addEventListener("click", function (e) {
        if (sidebar && sidebar.classList.contains("sidebar--open")) {
            if (!sidebar.contains(e.target) && e.target !== openBtn) {
                sidebar.classList.remove("sidebar--open");
            }
        }
    });

    // ────────────────────────────────────────────────────────────
    //  Message auto-dismiss after 5 seconds
    // ────────────────────────────────────────────────────────────

    var messages = document.querySelectorAll(".message");
    messages.forEach(function (msg) {
        setTimeout(function () {
            msg.style.opacity = "0";
            msg.style.transition = "opacity 0.3s ease";
            setTimeout(function () { msg.remove(); }, 300);
        }, 5000);
    });

    // ────────────────────────────────────────────────────────────
    //  Double-submit prevention
    // ────────────────────────────────────────────────────────────

    var entryForm = document.getElementById("entry-form");
    if (entryForm) {
        entryForm.addEventListener("submit", function () {
            var submitBtn = document.getElementById("submit-btn");
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.textContent = "Saving…";
            }
        });
    }

})();

