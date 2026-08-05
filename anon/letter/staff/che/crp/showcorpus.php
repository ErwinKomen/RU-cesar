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
   h3 {
     margin-left: auto;
     margin-right: auto;
     text-align: center;
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
  div.text table {
     font-size: 10px;
  }
  tr.header td {
	font-weight: bold;
	font-size: 12px;
  }

 </style>
</head>
<body>
<?php
/* define the directory */
$directory = "/che/crp/";
$nmsu = 'Texts made available by Ron Zacharski';

/* Start the table already */
echo "<p><h3>Nijmegen Parsed Corpus of Modern Chechen</h3>"
      . "<div class='text'>"
      . "<table><tr class='header'><td>#</td><td>Name</td>"
	. "<td>Title</td><td>Author</td><td>Source</td></tr>";

/* Get all the files with a .psdx.xml extension */
$srch = "*.psdx.xml";

$texts = glob($srch);

/* Are there any texts? */
if (count($texts) === 0) 
{
  echo '<tr><td>-1</td><td>Sorry!</td>' . 
       '<td>There are no [.psdx] texts available</td><td>NPCMC</td><td>' . 
       date("r") . '</td></tr>';
}
else
{
  /* Iterate through these files */
  for($i=0; $i<count($texts); $i++)
  {
	/* Determine the [Name] from the filename */
	$path_parts = pathinfo($texts[$i]);
	$name = $path_parts['basename'];

	/* Create a new XMLreader */
      $rdThis = new XMLReader();
	/* Read the XML file into the reader */
      $rdThis->open($texts[$i]);
	/* Move to the name of this text */
        $bTitle   = 0; $bBibl = 0;
	$strTitle = '(no title)';
	$strAuth  = '(no author)';
        $strBibl  = '(no source)';
        while ($rdThis->read() && (!$bTitle || !$bBibl))
        {
          if ($rdThis->nodeType == XMLReader::ELEMENT) 
          {
            $exp = $rdThis->expand();
            if ($exp->nodeName == 'titleStmt')
            {
              /* Get the title and the author attributes */
              $strTitle = $exp->getAttribute('title');
              $strAuth  = $exp->getAttribute('author');
              if ($strAuth == NULL) $strAuth = '-';
              $bTitle   = 1;
			}
            if ($exp->nodeName == 'sourceDesc')
            {
              /* Get the title and the author attributes */
              $strBibl = $exp->getAttribute('bibl');
              $bBibl = 1;
			}
          }
        }
        /* Remove the NMSU statement if it is in the bibl string */
        $iPos = stripos($strBibl, $nmsu);
        if ($iPos > 0)
        {
           /* Take it away */
           $strBibl = substr($strBibl, 0, $iPos-1);
        }

	/* Create a row for this file */  
	echo "<tr><td>" . $i . "</td>" 
             . "<td><a href='" . $texts[$i] . "'>" . $name . "</a></td>"
             . "<td nowrap>" . $strTitle . "</td><td>" . $strAuth . "</td><td>"
             . $strBibl . "</td>"
             . "</tr>";
  }
}
/* Close the table */
echo "</table></div>";

?>
</body>
</html>