/**
 * Pyxon Chatbot Widget – embed script.
 * Usage: <script src="https://your-server:8002/embed.js" data-base="https://your-server:8002"></script>
 * Or omit data-base to use the same origin as the script src.
 */
(function() {
  var script = document.currentScript;
  var base = (script && script.getAttribute('data-base')) || (script && script.src ? new URL(script.src).origin : '');
  if (!base) return;

  var iframe = document.createElement('iframe');
  iframe.src = base + '/widget';
  iframe.title = 'Chat';
  iframe.style.cssText = 'position:fixed;bottom:0;right:0;width:100%;height:100%;border:none;z-index:2147483646;';
  document.body.appendChild(iframe);
})();
