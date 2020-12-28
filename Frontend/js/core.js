function FedGate(url) {
	let dir = new Object();
	
	if (url == undefined) { //FOR DEVELOPMENT PURPOSE ONLY
		url = "http://localhost:9090/";
	}
	if (!url.endsWith("/")) {
		url += "/";
	}
	
	async function sendToAPI(action, callback, args, callbargs={}) {
		if (args.headers == undefined || Object.keys(args["headers"]).length == 0) {
			args.headers = {"Content-Type": "text/plain"} //{"Content-Type": "application/x-www-form-urlencoded"};
		}
		if (args.jsonRequest) {
			args.headers["Content-Type"] = "application/json";
		}
		
		let result;
		let response = await fetch(url + action, {"method": "POST", "credentials": "include", "cache": "force-cache", "headers": args.headers, "body": JSON.stringify(args.body)});
		if (args.jsonResponse) {
			result = await response.json();
		} else {
			result = await response.text();
		}
		if (Object.keys(callbargs).length == 0) {
			callback(result);
		} else {
			callback(result, callbargs)
		}
	}
	dir.sendToAPI = sendToAPI;
	
	function loggedIn(To, callbargs={}) {
		sendToAPI("loggedIn", To, {"jsonResponse": true}, callbargs);
	}
	dir.loggedIn = loggedIn;
	
	function getEntries(jsonObject, To, callbargs={}) {
		sendToAPI("getEntries", To, {body: jsonObject, jsonRequest: true, jsonResponse: true}, callbargs);
	}
	dir.getEntries = getEntries;
	
	function getDistinctEntries(jsonObject, To, callbargs={}) {
		sendToAPI("getDistinctEntries", To, {body: jsonObject, jsonRequest: true}, callbargs);
	}
	dir.getDistinctEntries = getDistinctEntries;
	
	function getUnique(jsonObject, To, callbargs={}) {
		
		if (jsonObject["column"] == undefined) {
			console.error("FedGate Client:\nTo receive all variations a key takes, the key itself must be specified in 'column'")
			To({"message": "columnMissing"});
			return false;
		}
		
		sendToAPI("getUnique", To, {body: jsonObject, jsonRequest: true, jsonResponse: true}, callbargs={});
	}
	dir.getUnique = getUnique;
	
	function changeEntry(jsonObject, To, callbargs={}) {
		sendToAPI("changeEntry", To, {body: jsonObject, jsonRequest: true, jsonResponse: true}, callbargs);
	}
	dir.changeEntry = changeEntry;
	
	function removeEntry(jsonObject, To, callbargs={}) {
		sendToAPI("removeEntry", To, {body: jsonObject, jsonRequest: true, jsonResponse: true}, callbargs);
	}
	dir.removeEntry = removeEntry;
	
	function addEntry(jsonObject, To, callbargs={}) {
		sendToAPI("addEntry", To, {body: jsonObject, jsonRequest: true, jsonResponse: true}, callbargs);
	}
	dir.addEntry = addEntry;
	
	function getTables(To, callbargs={}) {
		sendToAPI("getTables", To, {jsonRequest: true, jsonResponse: true}, callbargs);
	}
	dir.getTables = getTables;
	
	function exposeDriver(jsonObject, To, callbargs={}) {
		sendToAPI("exposeDriver", To, {body: jsonObject, jsonRequest: true, jsonResponse: true}, callbargs);
	}
	dir.exposeDriver = exposeDriver;
	
	function login(provider, To=function() {}, callbargs={}) {
		function callb(resp) {
			console.info("FedGate Client:\nRedirecting to '" + provider + "'s OAuth login page...");
			location.href = resp;
		}
		if (provider == undefined || provider == "") {
			console.error("FedGate Client:\nfunction 'login' called without providing a provider code. Call it like e.g.: `login(\"osm\") in order to log in with an OpenStreetMap account.");
			To();
		}
		sendToAPI("login/" + provider, callb, {}, callbargs);
	}
	dir.login = login;
	
	function logout(To, callbargs={}) {
		console.log("logging out");
		function callb(resp, callbargs) {
			if (resp.url != undefined) {
				console.info("FedGate Client:\nYou have been logged out!");
				console.info("FedGate Client:\nRedirecting to homepage...");
				location.href = resp.url;
			} else if (resp.message != undefined) {
				console.error("FedGate Client:\nYou weren't logged in!");
			}
			To(resp, callbargs);
		}
		sendToAPI("logout", callb, {}, callbargs);
	}
	dir.logout = logout;
	
	return dir;
}
