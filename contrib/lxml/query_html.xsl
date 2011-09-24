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
        <table border="in">
            <th class="surnames">
                <h2><xsl:value-of select="query/surnames/@title"/>
                (<xsl:value-of select="$surname-count"/>):</h2>
                <a name="surnames"/><xsl:apply-templates select="query/surnames"/>
            </th>
            <th class="places">
                 <h2><xsl:value-of select="query/places/@title"/>
                 (<xsl:value-of select="$place-count"/>):</h2>
                 <a name="places"/><xsl:apply-templates select="query/places"/>
            </th>
        </table>
        <div align="right"><xsl:value-of select="query/@footer"/>-<xsl:value-of select="query/log/@version"/></div>
        <div align="right">(<i><xsl:value-of select="query/log/@date"/></i>)</div>
    </body>
</html>

</xsl:template>

<xsl:template match="query/surnames">
    <xsl:for-each select="surname">
        <p><a href="#surnames">
        <i><b><xsl:value-of select="."/></b></i></a></p>
    </xsl:for-each>
</xsl:template>

<xsl:template match="query/places">
<xsl:choose>
    <xsl:when test="place">
        <xsl:for-each select="place">
            <p><a href="#places">
            <xsl:number value="position()" format="1"/>:
            <i><b><xsl:value-of select="."/></b></i></a></p>
        </xsl:for-each>
    </xsl:when>
</xsl:choose>
</xsl:template>

</xsl:stylesheet>
