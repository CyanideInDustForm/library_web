<?xml version="1.0" encoding="UTF-8"?>
<!-- static/xml/books.xsl — каталог книг, сортировка по названию -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>Книжный фонд — XML</title>
        <style>
          body { font-family: 'Segoe UI', Arial, sans-serif; margin: 2rem; background: #fffdf8; color: #3b2100; }
          h1 { border-left: 5px solid #e98527; padding-left: .6rem; }
          .meta { color: #8a6a3a; font-size: .9rem; }
          table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
          th, td { border: 1px solid #d9c39a; padding: .5rem .75rem; text-align: left; }
          th { background: #e98527; color: #fff8ee; }
          tr:nth-child(even) { background: #fdf3e2; }
          .back { display: inline-block; margin-top: 1rem; color: #a35a10; }
          .switch { display: inline-block; margin-left: 1rem; font-size: .9rem; }
        </style>
      </head>
      <body>
        <h1>Книжный фонд
          <span class="switch">(<a href="/xml/books.xml?sort=year">сортировка по году ↓</a>)</span>
        </h1>
        <p class="meta">Сформировано: <xsl:value-of select="/*/@generated"/> · <xsl:value-of select="count(/*/item)"/> изданий · сортировка: название (xsl:sort)</p>
        <table>
          <thead>
            <tr><th>Инв. №</th><th>Название</th><th>Автор</th><th>Год</th><th>ISBN</th></tr>
          </thead>
          <tbody>
            <xsl:for-each select="/*/item">
              <xsl:sort select="title"/>
              <tr>
                <td><xsl:value-of select="inventory"/></td>
                <td><xsl:value-of select="title"/></td>
                <td><xsl:value-of select="author"/></td>
                <td><xsl:value-of select="year"/></td>
                <td><xsl:value-of select="isbn"/></td>
              </tr>
            </xsl:for-each>
          </tbody>
        </table>
        <a class="back" href="/xml">← К XML-порталу</a>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
