const square = (n) => n * n;
console.log(square(3));

const greet = (name, greeting = "안녕 내이름은,") =>
  `${greeting} ${name}이야. 만나서 반가워`;
console.log(greet("김민영"));
console.log(greet("김철수", "내 소개를 할게, 나는"));

const isPassed = (score) => score >= 70;
console.log(isPassed(75));
