// JavaScript commun pour les Flow Salesforce

/**
 * Fonctions utilitaires réutilisables pour tous les Flow Salesforce
 */

function applyFlowStyling() {
  const flowEl = document.querySelector("flowruntime-flow");
  
  if (flowEl && flowEl.shadowRoot) {
    const style = document.createElement("style");
    style.textContent = "\n      /* Styles personnalisés pour le Flow */\n      button.slds-button_brand {\n        background-color: var(--primary) !important;\n        border: none !important;\n        border-radius: var(--radius-md) !important;\n        padding: 0.875rem 1.75rem !important;\n        font-weight: 600 !important;\n        color: white !important;\n        transition: all 0.3s ease !important;\n      }\n      button.slds-button_brand:hover {\n        background-color: var(--primary-dark) !important;\n        transform: translateY(-2px) !important;\n      }\n      input, select, textarea {\n        border-radius: var(--radius-md) !important;\n        border: 1px solid var(--border) !important;\n        padding: 0.875rem 1rem !important;\n      }\n    ";
    flowEl.shadowRoot.appendChild(style);
  }
}

function setupFlowObserver() {
  const flowEl = document.querySelector("flowruntime-flow");
  
  if (flowEl && flowEl.shadowRoot) {
    const observer = new MutationObserver(function(mutations) {
      const footerButtons = flowEl.shadowRoot.querySelectorAll("footer button");
      footerButtons.forEach(function(button) {
        if (button.textContent.includes("Finish") && !button.hasAttribute("data-enhanced")) {
          button.setAttribute("data-enhanced", "true");
          button.addEventListener("click", function() {
            console.log("Flow terminé avec succès !");
            // Ici on peut ajouter des actions personnalisées
          });
        }
      });
    });
    
    observer.observe(flowEl.shadowRoot, {
      childList: true,
      subtree: true
    });
  }
}

function showLoadingError() {
  const loadingElement = document.getElementById("flowLoading");
  if (loadingElement) {
    loadingElement.innerHTML = "<div style=\"color: red; text-align: center;\"><p>Erreur de chargement du Flow Salesforce</p></div>";
  }
}

// Utilitaires d'animation
function animateElements() {
  document.querySelectorAll(".animate-in").forEach(function(element, index) {
    element.style.animationDelay = (index * 0.1) + "s";
  });
}

// Initialisation commune (pas de logique Lightning ici)
document.addEventListener("DOMContentLoaded", function() {
  console.log("Utilitaires Salesforce Flow chargés");
  animateElements();
});