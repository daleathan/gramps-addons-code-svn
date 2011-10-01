<?xml version='1.0' encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<!--
   ===================================================================
GNU General Public License 2, or (at your option) any later version.
   ===================================================================
-->
<xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>

<xsl:variable name="surname-count" select="count(query/surnames/surname)"/>
<xsl:variable name="place-count" select="count(query/places/place)"/>

<xsl:template match="/">

<html>
    <head>
        <link rel="stylesheet" type="text/css" href="catalogue.css"/>
    </head>
    <body>
        <h1><xsl:value-of select="query/@title"/></h1>
        <h2><xsl:value-of select="query/surnames/@title"/>:<xsl:value-of select="$surname-count"/></h2>
        <form>
        <select name="slist">
           <xsl:for-each select="query/surnames/surname">
              <option>
                 <xsl:value-of select="."/>
              </option>
           </xsl:for-each>
        </select>
        </form>
        <h2><xsl:value-of select="query/places/@title"/>:<xsl:value-of select="$place-count"/></h2>
        <form>
        <select name="plist">
           <xsl:for-each select="query/places/place">
              <option>
                 <xsl:value-of select="."/>
              </option>
           </xsl:for-each>
        </select>
        </form>
        <div align="right"><xsl:value-of select="query/@footer"/>-<xsl:value-of select="query/log/@version"/></div>
        <div align="right">(<i><xsl:value-of select="query/log/@date"/></i>)</div>
        <div align="left"><b><xsl:value-of select="query/@date"/></b></div>
    </body>
</html>

</xsl:template>

</xsl:stylesheet>
