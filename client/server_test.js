const ws = new WebSocket('ws://localhost:8765');

ws.onopen = () => {
	document.getElementById('output').innerHTML = 'Подключено!<br>';
};

ws.onmessage = (event) => {
	document.getElementById('output').innerHTML += `${event.data}<br>`;
};

ws.onerror = () => {
	document.getElementById('output').innerHTML = 'Ошибка соединения<br>';
};

function send() {
	const msg = document.getElementById('msg').value;
	if (msg && ws.readyState === WebSocket.OPEN) {
		ws.send(msg);
		document.getElementById('output').innerHTML += `Вы: ${msg}<br>`;
		document.getElementById('msg').value = '';
	}
}
