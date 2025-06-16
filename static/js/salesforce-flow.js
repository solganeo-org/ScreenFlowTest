// JavaScript commun pour les Flow Salesforce

function initializeSalesforceFlow(config) {
  if (typeof $Lightning === "undefined") {
    console.error("Lightning framework non chargé");
    return;
  }
  
  $Lightning.use(config.apiName, function() {
    const loadingElement = document.getElementById("flowLoading");
    if (loadingElement) {
      loadingElement.style.display = "none";
    }
    
    $Lightning.createComponent("c:embeddedFlow", {}, "salesforceFlowContent");
  }, "https://solganeo--carboneio.sandbox.my.salesforce-sites.com");
}

function applyFlowStyling() {
  const flowEl = document.querySelector("flowruntime-flow");
  
  if (flowEl && flowEl.shadowRoot) {
    const style = document.createElement("style");
    style.textContent = "/* Styles personnalisés pour le Flow */";
    flowEl.shadowRoot.appendChild(style);
  }
}

document.addEventListener("DOMContentLoaded", function() {
  console.log("Page chargée - Flow Salesforce prêt");
  
  // Animation des éléments au chargement
  document.querySelectorAll(".animate-in").forEach(function(element, index) {
    element.style.animationDelay = (index * 0.1) + "s";
  });
});