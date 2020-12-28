var API = FedGate("http://localhost:8765");
var channel = "";
var region = "";
var loginologoutbtn = document.getElementById("loginologout");


API.loggedIn(function(m) {
	console.log(m)
	console.log(m.message == "userLoggedIn")
	if (m.message == "userLoggedIn") {
		console.log("logout code")
		loginologoutbtn.innerHTML = loginologoutbtn.getAttribute("logouttext");
		loginologoutbtn.state = "logout";
		console.log(loginologoutbtn.state)
	} else {
		loginologoutbtn.innerHTML = loginologoutbtn.getAttribute("logintext");
		loginologoutbtn.state = "login";
	}
});

document.getElementById("table").addEventListener("input", function(e) {
	API.getTables(
	listAutocompletionItems,
	{"id": "autocompleteTable"}
	); 
});
document.getElementById("category").addEventListener("input", function(e) {
	API.getUnique(
	{"channel": document.getElementById("table").value.trim().toLowerCase(), "column": "region"},
	listAutocompletionItems,
	{"id": "autocompleteCategory"}
	);
});

function listAutocompletionItems(out, args) {
	let elem = document.getElementById(args.id);
	elem.innerHTML = ""; //clean it
	
	out = out.message
	
	let lis = [];
	let index = 0;
	for (let i of out) {
		let e = new Object();
		let li = document.createElement("li");
		let t = document.createTextNode(i);
		
		li.appendChild(t);
		li.id = args.id + "_" + String(index);
		index += 1;
		li.addEventListener("click", function(e) {
			elem.previousSibling.value = elem.innerText;
			e.target = elem;
			hideAutocompletion(e);
		});
		lis.push(li);
	}
	
	for (let li of lis) {
		elem.appendChild(li);
	}
	elem.style.display = "block";
	document.addEventListener("click", hideAutocompletion);
}

function hideAutocompletion(e) {
	e.target.style = "";
	document.removeEventListener("click", hideSearchBox);
}

function loginologout() {
	if (loginologoutbtn.state == "login") {
		API.login("osm");
	} else {
		console.log("call:");
		API.logout(function() {});
	}
}

function buildItem(json) {
	let out = [];
	
	for (i in json) {
		out.add(`<div class='item' dataid='${json[i]["id"]}' channel=''>
					<button onclick='editItem(event.target)' class='editbtn'>✏️ &nbsp; Edit</button>
					<button onclick='changeItem(event.target)' class='hide sendbtn'>Send</button>
					<h1 class='editable' key='name'>${json[i]["name"]}</h1>
					<h2 class='editable' key='region'>${json[i]["region"]}</h2>
					<p>Shortcode: <input class='editable' key='shortcode' type='text' value='${json[i]["shortcode"]}' /></p>
					<p>Invitelink: <input class='editable' key='invitelink' type='text' value='${json[i]["invitelink"]}' /></p>
					<textarea class='editable' key='description'>${json[i]["description"]}</textarea>
				</div>`);
	}
	
	return out;

}

function listEntries(json) { document.getElementById("resultset").innerHTML = buildItem(json).join("\n"); }

function addNew() {
	let target = document.getElementById("resultset");
	target.innerHTML = buildItem({
	"id": "new",
	"channel": channel,
	"name": "e.g. OpenStreetMap Africa",
	"region": region,
	"shortcode": "e.g. osmafrica",
	"description": "e.g. OpenStreetMap Africa supergroup"
	}).join("\n") + target.innerHTML;
}

function editItem(elem) {
	let item = elem.parentElement;
	
	for (child of item.getElementsByClassName("editable")) {
		if (child.tagName.toLowerCase() == "h1" || child.tagName.toLowerCase() == "h2") {
			child.setAttribute("contenteditable", true);
		}
	}
	
	item.getElementsByClassName("sendbtn")[0].classList.remove("hide")
	
}

function messageInterpreter(m) {
	if (m == "userNotLoggedIn") { return {"text": "You are currently not logged in", "color": "red"} }
	if (m == "loggedOut") { return {"text": "Logged out successfully", "color": "green"} }
	if (m == "insufficientResultByDBDriver") { return {"text": "Internal error in driver", "color": "red"} }
	if (m == "noResult") { return {"text": "Here it is very very very quiet :(", "color": "grey"} }
	if (m == true) { return {"text": "Success", "color": "green"} }
	if (m == false) { return {"text": "Failure", "color": "red"} }
	
	return {"text": "An unknown error occurred!", "color": "red"}
}

function itemNotificator(json) {
	json = messageInterpreter(json["message"]);
	alert(json["text"]);
}

function changeItem(elem) {
	let item = elem.parentElement;
	let jsonObject = {"id": item.getAttribute("dataid"), "channel": channel};
	
	for (child of item.getElementsByClassName("editable")) {
		if (child.hasAttribute("key") == undefined) { continue; }
		
		let text = "";
		
		if (child.tagName.toLowerCase() == "h1" || child.tagName.toLowerCase() == "h2") {
			text = child.innerText;
		} else {
			text = child.value;
		}
		
		jsonObject[child.getAttribute("key")] = text;
	}
	
	API.changeEntry(jsonObject, itemNotificator);

}

function fetchChannels() {
	let channel = document.getElementById("table").value; // Containing the name of the social media plattform
	let region = document.getElementById("category").value; // Containing the name of the region
	channel = channel.toLowerCase().trim()
	region = region.toLowerCase().trim()
	
	API.getEntries({"channel": channel, "region": region}, listEntries);
}
