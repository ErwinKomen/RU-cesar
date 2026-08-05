<html>
<head>
 <title>NPCMC</title>
 <style type="text/css">
 body {
   /*background: #222222;*/
   background: #b7c8c7;
   font-family: sans-serif;
   font-size: 11px;
   margin-bottom:240px;
   }
   div.text {
     width: 700px;
     margin-top: 50px;
     margin-left: auto;
     margin-right: auto;
     padding: 10px;
     padding-left: 50px;
     padding-right: 50px;
     text-align: left;
     background: white;
     font-size: 10px;
     border: 2px solid black;
  }

 </style>
</head>
<body>
<?php
/* define the directory */
$directory = "/che/crp/";

/* Start the table already */
echo "<p><h3>Nijmegen Parsed Corpus of Modern Chechen</h3>"
      . "<div class='text'>"
      . "<table><tr><td>#</td><td>Name</td>"
	. "<td>Title</td><td>Author</td><td>Date</td></tr>";

/* Get all the files with a .psdx.xml extension */
/* $srch  = $directory . "*.xml"; */
$srch = "*.xml";

$texts = glob($srch);

/* ----------------------------------------------------------
echo "<tr><td>count</td><td>" . count($texts) . "</td></tr>";
   ---------------------------------------------------------- */

/* Iterate through these files */
for($i=0; $i<count($texts); $i++)
{
	/* Determine the [Name] from the filename */
	$path_parts = pathinfo($texts[$i]);
	$name = $path_parts['basename'];

	/* Create a new XMLreader */
      $rdThis = new XMLReader();
	/* Read the XML file into the reader */
      $rdThis->xml($texts[$i]);
	/* Move to the name of this text */
      while($rdThis->read() && $rdThis->name !== 'titleStmt');
	/* Check if we have a title */
	if ($rdThis->name === 'titleStmt') 
	{
        //Read the current child xml into a SimpleXMLElement
        $node = new SimpleXMLElement($rdThis->readOuterXML());
	  $strTitle = $node->title
	  $strAuth = $node->author
	}
 	else
	{
	  $strTitle = '(no title)'
	  $strAuth  = '(no author)'
	}

	/* Create a row for this file */  
	echo "<tr><td>" . $i . "</td>" 
             . "<td><a href='" . $texts[$i] . "'>" . $name . "</a></td>"
             . "<td>" . $strTitle . "</td><td>" . $strAuth . "</td><td>-</td>"
             . "</tr>";
}
/* Close the table */
echo "</table></div>";

?>
</body>
</html>