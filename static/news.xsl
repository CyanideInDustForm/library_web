<?xml version="1.0" encoding="UTF-8"?>
<!-- static/news.xsl — стилевая таблица для XML-лент сайта библиотеки.
     Подключается через <?xml-stylesheet?> в ответах /xml/*.xml -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>XML-данные библиотеки</title>
        <style>
          body { font-family: 'Segoe UI', Arial, sans-serif; margin: 2rem; background: #fffdf8; color: #3b2100; }
          h1 { border-left: 5px solid #e98527; padding-left: .6rem; }
          .meta { color: #8a6a3a; font-size: .9rem; }
          table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
          th, td { border: 1px solid #d9c39a; padding: .5rem .75rem; text-align: left; vertical-align: top; }
          th { background: #e98527; color: #fff8ee; }
          tr:nth-child(even) { background: #fdf3e2; }
          .back { display: inline-block; margin-top: 1rem; color: #a35a10; }
        </style>
      </head>
      <body>
        <h1>XML-данные: <xsl:value-of select="name(/*)"/></h1>
        <p class="meta">Сформировано: <xsl:value-of select="/*/@generated"/> · источник — база данных библиотеки</p>
        <table>
          <thead>
            <tr>
              <xsl:for-each select="/*/*[1]/*">
                <th><xsl:value-of select="name()"/></th>
              </xsl:for-each>
            </tr>
          </thead>
          <tbody>
            <xsl:for-each select="/*/*">
              <tr>
                <xsl:for-each select="*">
                  <td><xsl:value-of select="."/></td>
                </xsl:for-each>
              </tr>
            </xsl:for-each>
          </tbody>
        </table>
        <a class="back" href="/xml">← К странице XML-доступа</a>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
