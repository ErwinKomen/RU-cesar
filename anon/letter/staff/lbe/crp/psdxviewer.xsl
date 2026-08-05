<?xml version="1.0" encoding="utf-8" ?>

<xsl:stylesheet version="1.0"
                xmlns="http://www.w3.org/1999/xhtml"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xmlns:imdi="http://www.mpi.nl/IMDI/Schema/IMDI"
                xmlns:psdx="http://erwinkomen.ruhosting.nl/psdx"
                xmlns:mf="http://example.com/mf"
                exclude-result-prefixes="mf">

  <xsl:output method="html"
              encoding="UTF-8"
              omit-xml-declaration="yes"
              doctype-public="-//W3C//DTD XHTML 1.0 Strict//EN"
              doctype-system="http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"
              indent="yes"
              cdata-section-elements="script"/>
  <xsl:template match="/">
    <xsl:apply-templates select="TEI" />
  </xsl:template>

  <xsl:template match="/TEI">
    <html>
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
        <!--<script type="text/javascript" src="http://code.jquery.com/jquery-1.5.1.min.js"></script>-->
        <title>
          <xsl:value-of select="teiHeader/fileDesc/titleStmt/@title"/>
          (<xsl:value-of select="teiHeader/fileDesc/publicationStmt/@distributor"/>)
        </title>
        <style type="text/css">
          body {
          /*background: #222222;*/
          background: #b7c8c7;
          font-family: sans-serif;
          font-size: 12px;
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
          border: 2px solid black;
          }

          div.div {
          padding-left: 0px;
          padding-top: 10px;
          padding-bottom: 10px;
          }

          #metadata {
          font-family: sans-serif;
          width: 700px;
          font-size: 90%;
          margin-left: auto;
          margin-right: auto;
          margin-top: 5px;
          margin-bottom: 5px;
          background: #b4d4d1; /*#FCFFD0;*/
          border: 1px solid #628f8b;
          width: 40%;
          padding: 5px;
          }
          #metadata table {
          text-align: left;
          }

          #text {
          border: 1px solid #628f8b;
          width: 60%;
          max-width: 1024px;
          background: white;
          padding: 20px;
          padding-right: 100px;
          margin-top: 5px;
          margin-left: auto;
          margin-right: auto;
          color: #222;
          }
          .s {
          background: white;
          display: inline;
          border-left: 1px white solid;
          border-right: 1px white solid;
          }
          .s0 {
          background: white;
          display: inline;
          border-left: 1px white solid;
          border-right: 1px white solid;
          margin-top: 20px;
          }
          .s1 {
          background: white;
          display: inline;
          border-left: 1px white solid;
          border-right: 1px white solid;
          margin-left: 20px;
          margin-top: 5px;
          }
          .s:hover {
          background: #e7e8f8;
          border-left: 1px blue solid;
          border-right: 1px blue solid;
          }
          .s0:hover {
          background: #e7e8f8;
          border-left: 1px darkgreen solid;
          border-right: 1px blue solid;
          }
          .s1:hover {
          background: #e7e8f8;
          border-left: 1px gold solid;
          border-right: 1px blue solid;
          }
          .word {
          display: inline;
          color: black;
          position: relative;
          text-decoration: none;
          z-index: 24;
          }
          #text {
          border: 1px solid #628f8b;
          width: 60%;
          max-width: 1024px;
          background: white;
          padding: 20px;
          padding-right: 100px;
          margin-top: 5px;
          margin-left: auto;
          margin-right: auto;
          color: #222;
          }

          .word {
          display: inline;
          color: black;
          position: relative;
          text-decoration: none;
          z-index: 24;
          }

          .t {
          display: inline;
          text-decoration: none;
          z-index: 24;
          }

          .sn {
          display: inline;
          position: relative;
          color: red;
          text-decoration:none;
          }
          .sn>.synt  { display: none; font-size: 12px; font-weight: normal; }
          .sn:hover {
          /*text-decoration: underline;*/
          z-index: 25;
          background: #bfc0ed;
          text-decoration: underline;
          }
          .sn:hover>.synt {
          display: block;
          position: absolute;
          color: black;
          width: 500px;
          font-size: 11px;
          left: 2em;
          top: 2em;
          background: #b4d4d1; /*#FCFFD0;*/
          opacity: 0.9; filter: alpha(opacity = 90);
          border: 1px solid #628f8b;
          padding: 5px;
          text-decoration: none !important;
          }

          .word>.attributes { display: none; font-size: 12px; font-weight: normal; }
          .word:hover {
          /*text-decoration: underline;*/
          z-index: 25;
          }
          .word:hover>.t {
          background: #bfc0ed;
          text-decoration: underline;
          }

          .word:hover>.attributes {
          display: block;
          position: absolute;
          width: 320px;
          font-size: 12px;
          left: 2em;
          top: 2em;
          background: #b4d4d1; /*#FCFFD0;*/
          opacity: 0.9; filter: alpha(opacity = 90);
          border: 1px solid #628f8b;
          padding: 5px;
          text-decoration: none !important;
          }
          .attributes dt {
          color: #254643;
          font-weight: bold;
          }
          .attributes dd {
          color: black;
          font-family: monospace;
          }
          .attributes .wordid {
          display: inline-block:
          width: 100%;
          font-size: 75%;
          color: #555;
          font-family: monospace;
          text-align: center;
          }
          .event {
          padding: 10px;
          border: 1px solid #4f7d87;
          }
          .info pre {
          width: 800px;
          margin-left: auto;
          margin-right: auto;
          padding: 5px;
          display: inline-block;
          font-family: sans-serif;
          font-size: 11px;
          background: #ddd;
          border: 1px dashed red;
          }
	    div.info pre {
          margin-left: auto;
          margin-right: auto;
          }
          span.attrlabel {
          display: inline-block;
          color: #254643;
          font-weight: bold;
          width: 90px;
          }
          span.attrvalue {
          font-weight: 12px;
          font-family: monospace;
          }
          div#iewarning {
          width: 90%;
          padding: 10px;
          color: red;
          font-size: 16px;
          font-weight: bold;
          text-align: center;
          }
        </style>

      </head>
      <body>
        <xsl:comment>
          <![CDATA[[if lte IE 10]>
			<div id="iewarning">
				The PSDX viewer does not work properly with Internet Explorer, please consider upgrading to Mozilla Firefox instead. 
			</div>
			<![endif]]]>
        </xsl:comment>
        <div class="info">
          <xsl:apply-templates select="teiHeader" />
        </div>
        <div class="text">
          <xsl:apply-templates select="forestGrp/forest" />
        </div>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="eLeaf[@Type='Vern' or @Type='Punct']" mode="words">
    <span id="{../@Id}" class="word">
      <span class="t">
        <xsl:value-of select="@Text"/>
      </span>
      <span class="attributes">
        <span class="wordid">
          <xsl:value-of select="../@Id" />
        </span>
        <br />
        <span class="attrlabel">Lemma:</span>
        <span class="attrvalue">
          <xsl:value-of select="../fs/f[@name='l']/@value"/>
        </span>
        <br />
        <span class="attrlabel">PoS:</span>
        <span class="attrvalue">
          <xsl:value-of select="../@Label"/>
        </span>
        <br />
        <!-- treat all other features that are available -->
        <xsl:for-each select="../fs[@type != 'leaf']/f[@name != 'l']">
          <span class="attrlabel">
            <xsl:value-of select="./parent::fs/@type"/>/
            <xsl:value-of select="@name"/>:
          </span>
          <span class="attrvalue">
            <xsl:value-of select="@value"/>
          </span>
          <br />
        </xsl:for-each>
      </span>
    </span>
    <xsl:text> </xsl:text>
    <!-- TODO: implement @nospace check -->
  </xsl:template>

  <!-- Calculate the subtree from element [ndThis] downwards -->
  <xsl:template name="syntax">
    <xsl:param name="ndThis" />
    <xsl:param name="intLevel" />
    <xsl:choose>
      <!-- Treat <forest> nodes -->
      <xsl:when test="@forestId">
        <table>
          <xsl:text>(ROOT </xsl:text>
          <!-- Walk all <eTree> children -->
          <xsl:for-each select="$ndThis/child::eTree" >
            <tr>
              <xsl:call-template name="syntax">
                <xsl:with-param name="ndThis" select="."/>
                <xsl:with-param name="intLevel" select="$intLevel+1" />
              </xsl:call-template>
            </tr>
          </xsl:for-each>
          <xsl:text>)</xsl:text>
        </table>
      </xsl:when>
      <!-- Treat <eTree> nodes -->
      <xsl:when test="@Id">
          <!-- Test if this node has an <eLeaf> child -->
          <xsl:choose>
            <xsl:when test="child::eTree">
              <!-- Walk all <eTree> children -->
              <xsl:for-each select="$ndThis/child::eTree" >
                <xsl:choose>
                  <xsl:when test="not(eTree/eLeaf)">
                    <!-- Show opening bracket and syntactic @Label value -->
                    <span style="erwin">
                      <xsl:text>(</xsl:text>
                      <xsl:value-of select="@Label"/>
                      <xsl:text> </xsl:text>
                    </span>
                    <xsl:call-template name="syntax">
                      <xsl:with-param name="ndThis" select="."/>
                      <xsl:with-param name="intLevel" select="$intLevel+1"/>
                    </xsl:call-template>
                  </xsl:when>
                  <xsl:otherwise>
                    <tr>
                      <!-- Insert empty table cells depending on $intLevel -->
                      <td>
                        <xsl:attribute name="width">
                          <xsl:value-of select="$intLevel*5"/>
                        </xsl:attribute>
                      </td>

                      <!-- Show opening bracket and syntactic @Label value -->
                      <!--<td>-->
                        <xsl:text>(</xsl:text>
                        <xsl:value-of select="@Label"/>
                        <xsl:text> </xsl:text>
                      <!--</td>-->
                      <xsl:call-template name="syntax">
                        <xsl:with-param name="ndThis" select="."/>
                        <xsl:with-param name="intLevel" select="$intLevel+1"/>
                      </xsl:call-template>
                      <!--<td>-->
                        <!-- Show closing bracket -->
                        <xsl:text>)</xsl:text>
                      <!--</td>-->
                    </tr>
                  </xsl:otherwise>
                </xsl:choose>
              </xsl:for-each>
            </xsl:when>
            <xsl:otherwise>
              <xsl:value-of select="eLeaf/@Text" />
              <span>
                <!-- Show closing bracket -->
                <xsl:text>)</xsl:text>
              </span>
            </xsl:otherwise>
          </xsl:choose>
      </xsl:when>
      <!-- Treat <eLeaf> nodes -->
      <!--
    <xsl:when test="@Type = 'Vern' or @Type='Punct'">
      <xsl:value-of select="@Text"/>
    </xsl:when>
    -->
    </xsl:choose>
    <!--
  <xsl:apply-templates />
  -->
  </xsl:template>
  

  <xsl:template match="forest">
    <!-- Check if a section or paragraph should start here -->
    <xsl:choose>
      <xsl:when test="@Section">
        <h1>section</h1>
        <div class="s0">
          <span class="sn">
            <xsl:value-of select="@forestId" />
            <span class="synt">
              <xsl:apply-templates select="descendant::div" mode="words" />
              <xsl:call-template name="syntax">
                <xsl:with-param name="ndThis" select="." />
                <xsl:with-param name="intLevel">1</xsl:with-param>
              </xsl:call-template>
            </span>
          </span>

          <xsl:text> </xsl:text>
          <xsl:apply-templates select="descendant::eLeaf" mode="words" />
        </div>
      </xsl:when>
      <xsl:when test="count(@Para) > 0 and not(@Section)">
        <br>
        </br>
        <div class="s1">
          <span class="sn">
            <xsl:value-of select="@forestId" />
            <span class="synt">
              <xsl:apply-templates select="descendant::div" mode="words" />
              <xsl:call-template name="syntax">
                <xsl:with-param name="ndThis" select="." />
                <xsl:with-param name="intLevel">1</xsl:with-param>
              </xsl:call-template>
            </span>
          </span>

          <xsl:text> </xsl:text>
          <xsl:apply-templates select="descendant::eLeaf" mode="words" />
        </div>
      </xsl:when>
      <xsl:otherwise>
        <div class="s">
          <span class="sn">
            <xsl:value-of select="@forestId" />
            <span class="synt">
              <xsl:apply-templates select="descendant::div" mode="words" />
              <xsl:call-template name="syntax">
                <xsl:with-param name="ndThis" select="." />
                <xsl:with-param name="intLevel">1</xsl:with-param>
              </xsl:call-template>
            </span>
          </span>

          <xsl:text> </xsl:text>
          <xsl:apply-templates select="descendant::eLeaf" mode="words" />
        </div>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="div" mode="words">
    <xsl:if test="@lang='eng'">
      <p>
        <xsl:apply-templates />
      </p>
    </xsl:if>
    <xsl:if test="@lang!='eng'">
      <!-- do NOT give any output -->
    </xsl:if>
  </xsl:template>

  <xsl:template match="teiHeader">
      <pre>
        <table align="center">
          <tr>
            <td>title</td>
            <td>
              <xsl:value-of select="fileDesc/titleStmt/@title" />
            </td>
          </tr>
          <tr>
            <td>author</td>
            <td>
              <xsl:value-of select="fileDesc/titleStmt/@author" />
            </td>
          </tr>
          <tr>
            <td>distributor</td>
            <td>
              <xsl:value-of select="fileDesc/publicationStmt/@distributor"/>
            </td>
          </tr>
          <tr>
            <td>language (name)</td>
            <td>
              <xsl:value-of select="profileDesc/langUsage/language/@name" />
            </td>
          </tr>
          <tr>
            <td>language (id)</td>
            <td>
              <xsl:value-of select="profileDesc/langUsage/language/@ident" />
            </td>
          </tr>
          <tr>
            <td>source</td>
            <td>
              <xsl:value-of select="fileDesc/sourceDesc/@bibl" />
            </td>
          </tr>
          <tr>
            <td>date (original)</td>
            <td>
              <xsl:value-of select="profileDesc/langUsage/creation/@original" />
            </td>
          </tr>
          <tr>
            <td>subtype</td>
            <td>
              <xsl:value-of select="profileDesc/langUsage/creation/@subtype" />
            </td>
          </tr>
          <tr>
            <td>genre</td>
            <td>
              <xsl:value-of select="profileDesc/langUsage/creation/@genre" />
            </td>
          </tr>
        </table>
      </pre>
  </xsl:template>

</xsl:stylesheet>
