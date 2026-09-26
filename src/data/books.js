export const bookChapters = {
  zechariah: { 
    title: 'Zechariah',
    chapters: [
      { chapter: '4', verses: ['Zechariah 4 v 6', 'Zechariah 4 v 7'] },
      { chapter: '6', verses: ['Zechariah 6 v 1–15'] },
      { chapter: '7', verses: ['Zechariah 7 v 1–14', 'Zechariah 7 v 5', 'Zechariah 7 v 9', 'Zechariah 7 v 10'] },
      { chapter: '8', verses: ['Zechariah 8 v 1–23', 'Zechariah 8 v 4', 'Zechariah 8 v 5', 'Zechariah 8 v 8', 'Zechariah 8 v 13', 'Zechariah 8 v 14'] },
      { chapter: '9', verses: ['Zechariah 9 v 1–17', 'Zechariah 9 v 9', 'Zechariah 9 v 10', 'Zechariah 9 v 16'] },
    ]
  },
  acts: {
    title: 'Acts',
    chapters: [
      { chapter: '22', verses: ['Acts 22 v 1–30', 'Acts 22 v 25'] },
      { chapter: '23', verses: ['Acts 23 v 1–22', 'Acts 23 v 11', 'Acts 23 v 21–22', 'Acts 23 v 23–35'] },
      { chapter: '24', verses: ['Acts 24 v 1–27'] },
    ]
  },
  job: {
    title: 'Job',
    chapters: [
      { chapter: '29', verses: ['Job 29 v 13–25'] },
      { chapter: '30', verses: ['Job 30 v 1–15'] },
    ]
  },
  haggai: { title: 'Haggai', chapters: [{ chapter: '1', verses: ['Haggai 1 v 1', 'Haggai 1 v 12', 'Haggai 1 v 14'] }, { chapter: '2', verses: ['Haggai 2 v 2', 'Haggai 2 v 23'] }] },
  ezra: { title: 'Ezra', chapters: [{ chapter: '3', verses: ['Ezra 3 v 2', 'Ezra 3 v 8'] }, { chapter: '5', verses: ['Ezra 5 v 2'] }] },
  isaiah: { title: 'Isaiah', chapters: [{ chapter: '30', verses: ['Isaiah 30 v 15–16'] }, { chapter: '40', verses: ['Isaiah 40 v 29–31'] }] },
  psalm: { title: 'Psalm', chapters: [{ chapter: '20', verses: ['Psalm 20 v 7'] }, { chapter: '33', verses: ['Psalm 33 v 16 - 17'] }] },
};

export const allBooks = Object.keys(bookChapters);