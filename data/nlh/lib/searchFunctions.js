/*
This search routine is based on the free Recon Search Engine
by Jerry Bradenbaugh (http://www.serve.com/hotsyte/)
alterations have been made by Marc Reed (http://www.marcreed.com)
og paal m �stby (www.pdctangen.no)
This script may be used for free
*/

// Define global variables

// the maxPages variable determines how
// many results are displayed per page:
var maxPages = 10;
// Antall tegn som vises pr treff
var showNumChar = 400;

var allMatch = new Array();
var phraseMatch = new Array();							
var anyMatch = new Array();
var urlMatch = new Array();
var indexer = 0;
var srcCrit = "any"
var count = 0;
var start = 0;
var urlTest = false;


//Search Results page should call this function
function doSearch() {

	fullEntry = getQueryString('searchField');
	filteredEntry = ""
	//Look for ++(clean up multiple spaces)
	var PlusSigns = "\+\+"
	while (fullEntry.indexOf(PlusSigns) >= 0) {
		fullEntry=fullEntry.replace(/\+\+/, "+")
	}
	
	//Isolate search term(s) and convert "+" to spaces
	for (i=0; i<fullEntry.length; i++) {
		if ((fullEntry.charAt(i) == "&")||(fullEntry.charAt(i) == "#")) {
			break
		}
		if (fullEntry.charAt(i) == "+") {
			filteredEntry = (filteredEntry+" ")
		}else {
			filteredEntry = (filteredEntry+(fullEntry.charAt(i)))
		}
	}
	
	if (filteredEntry.indexOf("#") > -1) filteredEntry = filteredEntry.substring(0, filteredEntry.indexOf("#"));
	validate(filteredEntry);
}

//This generic function will return the value of a QueryString
function getQueryString(Val) {
	thisURLparamStr = document.location.search;
	//chop "?" off thisURLparamStr
	if (thisURLparamStr.charAt(0) == "?") thisURLparamStr = thisURLparamStr.substring(1, thisURLparamStr.length);
	returnStr = "";
	if (thisURLparamStr != "") {
		//Build array out of thisURLparamStr using "&" as delimiter
		divide1=(thisURLparamStr.split("&"))
		for (i=0; i < divide1.length; i++) {
			divide2 = divide1[i].split("=")
			if (unescape(divide2[0]) == Val) {
				returnStr = unescape(divide2[1]);
			}
		}
	}
	return returnStr;
}

//Determine any word/all words/phrase search
function validate(text) {

	var entry = text;
	
	//clean up spaces at beginning of string
	while (entry.charAt(0) == ' ') {					
		entry = entry.substring(1,entry.length);
	}
	//clean up spaces at end of string
	while (entry.charAt(entry.length - 1) == ' ') {
		entry = entry.substring(0,entry.length - 1);
	} 
	
	if ((entry.charAt(0) == "+")||(getQueryString('srcriteria') == "all")) {
		entry = (entry.charAt(0) == "+")? entry.substring(1,entry.length):entry;
		srcCrit = "all"
	}
	if (entry.substring(0,4) == "url:") {
		entry = entry.substring(5,entry.length);
		srcCrit = "url"
	}
	//If user wants exact phrase
	if (((entry.charAt(0) == "\"")&&(entry.charAt((entry.length)-1) == "\""))||(getQueryString('srcriteria') == "phrase")){
		while (entry.indexOf("\"") > -1) {
			entry=entry.replace(/\"/, "")
		}
		srcCrit = "phrase"
	}
	if (entry.length < 3) {
		alert("Please type a word larger than three characters.");
		return;
	}
	convertString(entry, text);
}


// If not exact phrase, split the entry string into an array
function convertString(reentry, text) {
	//If user wants exact phrase
	if (srcCrit == "phrase") {
		searchTerm = reentry;
		requirePhrase(searchTerm, text);
		return;
	}
	searchArray = reentry.split(" ");
	if (srcCrit == "any") { allowAny(searchArray, text); return; }
	if (srcCrit == "all") { requireAll(searchArray, text); return; }
	if (srcCrit == "url") { parseURL(searchArray, text); return; }	
}


//*************************************************************
// This function merges title, brief description, page content,
// keywords and returns all-caps string
//*************************************************************
function mergeCaps(str1, str2, str3) {

	mergeStr = "";
	// join str2 (brief description) and str3 (rest of page text)
	// if page content is longer than brief description length,
	// then str2 ends "..."
	// if str2 ends "..." remove dots
	if ((str2.length > 0) && (str2.charAt(0) != " ")) str2 = " " + str2;
	if (str2.substring(str2.length - 3, str2.length) == "...") {
			mergeString = str2.substring(0, str2.length - 3).concat(str3);
	} else {
			mergeString = str2.concat(str3);
	}
	mergeString = str1 + mergeString
	//to make search case-insensitive, convert to all caps
	return mergeString.toUpperCase();

}

//*************************************************************************
// This function will parse the URL search string and change a name/value pair
//*************************************************************************
function changeParam(whichParam, newVal) {
	newParamStr = "";
	thisURLstr = document.location.href.substring(0, document.location.href.indexOf("?"));
	thisURLparamStr = document.location.href.substring(document.location.href.indexOf("?") + 1, document.location.href.length);
	//Build array out of thisURLparamStr using "&" as delimiter
	divide1=(thisURLparamStr.split("&"))
	for (cnt=0; cnt < divide1.length; cnt++) {
		divide2 = divide1[cnt].split("=")
		if (divide2[0] == whichParam) {
			// if we find whichParam in thisURLparamStr replace whichParam's value with newVal
			newParamStr = newParamStr + divide2[0] + "=" + escape(newVal) + "&";
		} else {
			//leave other parameters intact
			newParamStr = newParamStr + divide2[0] + "=" + divide2[1] + "&";
		}
	}
	//strip off trailing ampersand
	if (newParamStr.charAt(newParamStr.length - 1) == "&") newParamStr = newParamStr.substring(0, newParamStr.length - 1);
	//apply new URL
 	return(thisURLstr + "?" + newParamStr);
}


//*************************************************************
// Sorts search results based on 1.Number of hits 2.aplhabetically
//*************************************************************
function compare(a, b) {
	if (parseInt(a) - parseInt(b) != 0) {
		return parseInt(a) - parseInt(b)
	}else {
		var aComp = a.substring(a.indexOf("|") + 1, a.length)
		var bComp = b.substring(b.indexOf("|") + 1, b.length)
		if (aComp < bComp) {return -1}
		if (aComp > bComp) {return 1}
		return 0
	}
}


//Evoked if user searches ANY WORDS
function allowAny(t, text) {
	var OccurNum = 0;
	for (i = 0; i < profiles.length; i++) {
		//strip url out of search string
		var refineElement = "";
		var splitline = profiles[i].split("|");
		refineElement = mergeCaps(splitline[0], splitline[1], splitline[2])
		OccurNum = 0;
		
		for (j = 0; j < t.length; j++) {
			
			eval("myRE = /" + t[j] + "/gi");
			OccurArray = refineElement.match(myRE);
			if (OccurArray != null) OccurNum = OccurNum + OccurArray.length;
			
		}
		if (OccurNum > 0) {
			anyMatch[indexer] = (0-OccurNum) + "|" + profiles[i];
			indexer++;
		}
	}

	if (anyMatch.length == 0) {						// If no matches are found, print a no match
		noMatch(text);							// HTML document
		return;
	}
	else { formatResults(anyMatch, text); }					// Otherwise, generate a results document
}

//Evoked if user searches ALL WORDS
function requireAll(t, text) {
	var OccurNum = 0;
	for (i = 0; i < profiles.length; i++) {
		var allConfirmation = true;
		var refineAllString = "";
		var splitline = profiles[i].split("|");
		refineAllString = mergeCaps(splitline[0], splitline[1], splitline[2])
		OccurNum = 0;
		
		for (j = 0; j < t.length; j++) {
			eval("myRE = /" + t[j] + "/gi");
			OccurArray = refineAllString.match(myRE);
			if (OccurArray != null) {
				OccurNum = OccurNum + OccurArray.length;
			} else {
				allConfirmation = false;
			}
			
		}
		
		if (allConfirmation) {
			allMatch[indexer] = (0-OccurNum) + "|" + profiles[i];
			indexer++;
			}
		}
	if (allMatch.length == 0) {
		noMatch(text);
		return;
	} else {
		formatResults(allMatch, text);
	}
}



//If user wants exact phrase
function requirePhrase(t, text) {
	for (i = 0; i < profiles.length; i++) {
		var allConfirmation = true;
		//strip url out of search string
		var refineAllString = "";
		var splitline = profiles[i].split("|");
		refineAllString = mergeCaps(splitline[0], splitline[1], splitline[2])
		var allElement = t.toUpperCase();
		var OccurNum = 0;
		
		eval("myRE = /" + t + "/gi");
		OccurArray = refineAllString.match(myRE);
		if (OccurArray != null) {
			OccurNum = OccurNum + OccurArray.length;
			phraseMatch[indexer] = (0-OccurNum) + "|" + profiles[i];
			indexer++;
		}

	}

	if (phraseMatch.length == 0) {
		noMatch(text);
		return;
	}
	else { formatResults(phraseMatch, text); }
}



function parseURL(u, text) {							 	// Incite the search, looking only in the URL portion of the string
	for (i = 0; i < profiles.length; i++) {		
		var urlConfirmation = true;		
		var anyURL = profiles[i].toUpperCase();
		//strip url out of search string
		var splitline = anyURL.split("|");
		var refineAnyURL = splitline[splitline.length - 1];
		var OccurNum = 0;
		for (j = 0; j < u.length; j++) { 
			var urlPart = u[j].toUpperCase();
			if (refineAnyURL.indexOf(urlPart) != -1 && (urlConfirmation)) { 
				urlConfirmation = false;
				urlMatch[indexer] = (0-OccurNum) + "|" + profiles[i];
				indexer++;
			}
		}
	}
	if (urlMatch.length == 0) {
		noMatch(text);
		return;
	}
	else {
		urlTest = true;
		formatResults(urlMatch, text, urlTest);
	}
}

//*************************************************************
// Format no-results page
//*************************************************************
function noMatch(text) {								// Dyanmic HTML page with no results
	document.writeln("<a name=\"top_of_page\"></a><h3>Resultat av friteksts�k</h3>");
	document.writeln("<h4><hr size=\"1\"><b>'" + text + "' ingen treff.<hr size=\"1\"><h4>");
	return true;
	}

//*************************************************************
// Format successfull search results page
//*************************************************************
function formatResults(passedArray, text, urlTest) {
	results = passedArray;
	pgRange = (getQueryString("range") != "")? parseInt(getQueryString("range")):1;
	document.writeln("<a name=\"top_of_page\"></a><h3>Resultat av friteksts&oslash;k</h3>");
	document.writeln("<h4><hr size=\"1\">S&oslash;kestreng: " + text + "<br>");
	document.writeln("Antall treff: "+ passedArray.length + "");
	document.writeln("<hr size=\"1\"></h4>");
	thisPg = 1;
	endPg = passedArray.length;
	if (passedArray.length > maxPages) {
		thisPg = (maxPages * pgRange) - (maxPages - 1);
		endPg = (parseInt(thisPg + (maxPages - 1)) < passedArray.length)? parseInt(thisPg + (maxPages - 1)):passedArray.length;
		document.writeln(thisPg + " - " + endPg + " av " + passedArray.length);
	}
	document.writeln("<dl style=\"font-family:verdana\">");
	passedArray.sort(compare);
	wrdArray = (srcCrit != "phrase")? text.split(" "):new Array(text);
	if (urlTest) {
		for (i = 0; i < passedArray.length ; i++) {
			divide = passedArray[i].split("|"); 			// Print each URL result as a unit of a definition list
			document.writeln("<dt>" + "<a href=\""+divide[4]+ "\" target=\"_self\">" + divide[4] + "</a></dt>");
			document.writeln("<dd>" + divide[2] + "</dd><br><br>");
		}
	}
	else {
	
		for (i = (thisPg - 1); i < endPg; i++) {
			divide = passedArray[i].split("|"); 			// Print each profile result as a unit of a definition list
			
			for (j=0; j<wrdArray.length; j++) {
				eval("myRE1 = /" + wrdArray[j] + "/gi");
				regArr = null;
				regArr = divide[2].match(myRE1);
				if (regArr != null) {
					//look for uniqueness in regArr
					beenThere = new Array();
					for (k=0; k<regArr.length; k++) {
						beenhere = 0; 
						for (l=0; l<beenThere.length; l++) {
							if (beenThere[l] == regArr[k]) {
								beenhere = 1;
								//break;
							}
							
						}
						if (beenhere == 0) {
							beenThere[beenThere.length] = regArr[k];
							eval("myRE2 = /"+regArr[k]+"/g");
							divide[2] = divide[2].replace(myRE2, "<\|>" + regArr[k] + "<\/\|>");
						}
					}
				}
			}

			myRE3 = /\<\|\>/g;
			myRE4 = /\<\/\|\>/g;
			divide[2] = divide[2].replace(myRE3, "<font color=red>");
			divide[2] = divide[2].replace(myRE4, "</font>");

			document.writeln("<dt><a href=\""+divide[4]+"\" target=\"_self\"><b>" + divide[1] + "</b></a><\dt>");
			/*  Trukket ut X f�rste tegn fra resultatarray */
			fdev = divide[2].substring(0,showNumChar );
			document.writeln("<dd>" + fdev + "</dd><br><br>");
		}
		
	}
	document.writeln("</dl>");				// Finish the HTML document

	//write results page numbers
	if (passedArray.length > maxPages) {
		pgNum = parseInt(passedArray.length/maxPages);
		if (passedArray.length/maxPages > pgNum) pgNum++;
		pgLinks = "g� til side: ";
		for (i=0; i < pgNum; i ++) {
			locationStr = (location.href.indexOf("&range=") > -1)? changeParam("range", parseInt(i + 1)):location.href + "&range=" + parseInt(i + 1);
			pgLinks += (parseInt(i + 1) != pgRange)? "<a href=\"" + locationStr + "\">" + (i + 1) + "</a> ":"<b>" + (i + 1) + "</b> ";
		}
		document.writeln(pgLinks + "<hr size=\"1\">");
	} 
	clearOut();
}

function clearOut() {								// Clear the arrays and variables generated from the current search
	allMatch.length = 0;	anyMatch.length = 0;
	urlMatch.length = 0;	divide.length = 0;
	indexer = 0;	all = false; 	urlTest = false;
}
	
	