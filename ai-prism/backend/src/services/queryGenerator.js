class QueryGenerator {
  static generate(brandName) {
    const brand = String(brandName || '').trim();
    return {
      brand,
      categories: {
        overview: [
          `What is ${brand}?`,
          `${brand} company overview`,
          `Who founded ${brand}?`,
          `${brand} leadership`
        ],
        comparisons: [
          `Top competitors of ${brand}`,
          `${brand} vs competitors`,
          `Is ${brand} a leader in its market?`
        ],
        products: [
          `Best products by ${brand}`,
          `${brand} product reviews`,
          `${brand} pricing`
        ],
        reputation: [
          `${brand} news coverage`,
          `${brand} customer reviews`,
          `Is ${brand} trustworthy?`
        ],
        influence: [
          `Which publishers write about ${brand}?`,
          `Media coverage analysis for ${brand}`
        ]
      }
    };
  }
}

module.exports = { QueryGenerator };
