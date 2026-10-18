<?xml version="1.0" encoding="UTF-8"?>
<!-- static/xml/events.xsl — афиша мероприятий с выделением дат и свободных мест -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>Афиша мероприятий — XML</title>
        <style>
          body { font-family: 'Segoe UI', Arial, sans-serif; margin: 2rem; background: #fffdf8; color: #3b2100; }
          h1 { border-left: 5px solid #e98527; padding-left: .6rem; }
          .meta { color: #8a6a3a; font-size: .9rem; }
          .event { border: 1px solid #d9c39a; border-left: 5px solid #e98527; border-radius: 6px;
                   padding: 1rem; margin: 1rem 0; background: #fff; }
          .event h2 { margin: 0 0 .3rem; font-size: 1.15rem; }
          .date { color: #a35a10; font-weight: 600; }
          .free { float: right; font-weight: 700; color: #2e7d32; }
          .none { float: right; font-weight: 700; color: #b3261e; }
          .back { display: inline-block; margin-top: 1rem; color: #a35a10; }
        </style>
      </head>
      <body>
        <h1>Афиша мероприятий</h1>
        <p class="meta">Сформировано: <xsl:value-of select="/*/@generated"/> · <xsl:value-of select="count(/*/item)"/> мероприятий</p>
        <xsl:for-each select="/*/item">
          <xsl:sort select="date"/>
          <div class="event">
            <xsl:choose>
              <xsl:when test="free &gt; 0">
                <span class="free">свободно мест: <xsl:value-of select="free"/></span>
              </xsl:when>
              <xsl:otherwise>
                <span class="none">мест нет</span>
              </xsl:otherwise>
            </xsl:choose>
            <h2><xsl:value-of select="title"/></h2>
            <div class="date"><xsl:value-of select="date"/> · <xsl:value-of select="place"/></div>
            <p><xsl:value-of select="description"/></p>
            <div class="meta">Всего мест: <xsl:value-of select="seats"/></div>
          </div>
        </xsl:for-each>
        <a class="back" href="/xml">← К XML-порталу</a>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
