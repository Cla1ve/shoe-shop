PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE Roles (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO Roles VALUES(1,'Администратор');
INSERT INTO Roles VALUES(2,'Менеджер');
INSERT INTO Roles VALUES(3,'Клиент');
CREATE TABLE Users (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    login     TEXT NOT NULL UNIQUE,
    full_name TEXT NOT NULL,
    role_id   INTEGER NOT NULL
              REFERENCES Roles(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
INSERT INTO Users VALUES(1,'masokolova','Соколова Мария Андреевна',1);
INSERT INTO Users VALUES(2,'anpetrov','Петров Алексей Николаевич',2);
INSERT INTO Users VALUES(3,'ovkuznetsova','Кузнецова Ольга Викторовна',2);
INSERT INTO Users VALUES(4,'isivanov','Иванов Сергей Игоревич',3);
INSERT INTO Users VALUES(5,'edsmirnova','Смирнова Екатерина Дмитриевна',3);
INSERT INTO Users VALUES(6,'dovolkov','Волков Дмитрий Олегович',3);
INSERT INTO Users VALUES(7,'apmorozova','Морозова Анна Павловна',3);
INSERT INTO Users VALUES(8,'asnovikov','Новиков Артём Сергеевич',3);
INSERT INTO Users VALUES(9,'eifedorova','Фёдорова Елена Ивановна',3);
INSERT INTO Users VALUES(10,'palebedev','Лебедев Павел Андреевич',3);
INSERT INTO Users VALUES(11,'guest1','Громов Игорь Станиславович',3);
INSERT INTO Users VALUES(12,'guest2','Орлова Татьяна Юрьевна',3);
CREATE TABLE Categories (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO Categories VALUES(1,'Женская обувь');
INSERT INTO Categories VALUES(2,'Мужская обувь');
INSERT INTO Categories VALUES(3,'Детская обувь');
INSERT INTO Categories VALUES(4,'Спортивная обувь');
CREATE TABLE Manufacturers (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO Manufacturers VALUES(1,'Salamander');
INSERT INTO Manufacturers VALUES(2,'Rieker');
INSERT INTO Manufacturers VALUES(3,'Ecco');
INSERT INTO Manufacturers VALUES(4,'Camper');
INSERT INTO Manufacturers VALUES(5,'Zenden');
INSERT INTO Manufacturers VALUES(6,'Converse');
INSERT INTO Manufacturers VALUES(7,'Skechers');
INSERT INTO Manufacturers VALUES(8,'Котофей');
INSERT INTO Manufacturers VALUES(9,'Adidas');
INSERT INTO Manufacturers VALUES(10,'Reima');
INSERT INTO Manufacturers VALUES(11,'Nike');
INSERT INTO Manufacturers VALUES(12,'Puma');
INSERT INTO Manufacturers VALUES(13,'Hoka');
INSERT INTO Manufacturers VALUES(14,'Asics');
CREATE TABLE Sizes (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    value INTEGER NOT NULL UNIQUE CHECK (value BETWEEN 15 AND 60)
);
INSERT INTO Sizes VALUES(1,28);
INSERT INTO Sizes VALUES(2,29);
INSERT INTO Sizes VALUES(3,30);
INSERT INTO Sizes VALUES(4,31);
INSERT INTO Sizes VALUES(5,32);
INSERT INTO Sizes VALUES(6,33);
INSERT INTO Sizes VALUES(7,34);
INSERT INTO Sizes VALUES(8,35);
INSERT INTO Sizes VALUES(9,36);
INSERT INTO Sizes VALUES(10,37);
INSERT INTO Sizes VALUES(11,38);
INSERT INTO Sizes VALUES(12,39);
INSERT INTO Sizes VALUES(13,40);
INSERT INTO Sizes VALUES(14,41);
INSERT INTO Sizes VALUES(15,42);
INSERT INTO Sizes VALUES(16,43);
INSERT INTO Sizes VALUES(17,44);
INSERT INTO Sizes VALUES(18,45);
INSERT INTO Sizes VALUES(19,46);
CREATE TABLE Products (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    category_id     INTEGER NOT NULL
                    REFERENCES Categories(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    manufacturer_id INTEGER NOT NULL
                    REFERENCES Manufacturers(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    description     TEXT,
    composition     TEXT,
    price           REAL NOT NULL CHECK (price >= 0),
    image           TEXT,
    UNIQUE (name, manufacturer_id)
);
INSERT INTO Products VALUES(1,'Туфли-лодочки Classic',1,1,'Классические туфли на устойчивом каблуке 6 см','Натуральная кожа, подкладка из кожи, подошва каучук',8990.0,'IMG_001.jpg');
INSERT INTO Products VALUES(2,'Ботильоны Chelsea Woman',1,2,'Ботильоны с эластичными вставками по бокам','Натуральная кожа, текстильная подкладка, подошва ТЭП',11990.0,'IMG_002.jpg');
INSERT INTO Products VALUES(3,'Балетки Soft Flat',1,3,'Мягкие балетки на каждый день','Мягкая натуральная кожа, кожаная стелька',7490.0,'IMG_003.jpg');
INSERT INTO Products VALUES(4,'Сапоги зимние Nordic',1,2,'Тёплые сапоги до колена','Натуральная кожа, мех, подошва ТЭП',14990.0,'IMG_004.jpg');
INSERT INTO Products VALUES(5,'Босоножки Summer Strap',1,4,'Летние босоножки с ремешком на щиколотке','Натуральная кожа, подошва ЭВА',9490.0,'IMG_005.jpg');
INSERT INTO Products VALUES(6,'Лоферы City',1,3,'Лоферы для офиса и города','Натуральная кожа, подошва полиуретан',10490.0,'IMG_006.jpg');
INSERT INTO Products VALUES(7,'Ботинки Trek Lady',1,1,'Демисезонные ботинки с мембраной','Нубук, мембрана, подошва резина',12990.0,'IMG_007.jpg');
INSERT INTO Products VALUES(8,'Сандалии Beach',1,5,'Лёгкие сандалии для лета','Искусственная кожа, текстиль',3490.0,'IMG_008.jpg');
INSERT INTO Products VALUES(9,'Туфли на каблуке Evening',1,5,'Вечерние туфли, каблук 8 см','Искусственная кожа, подошва ТПУ',4990.0,'IMG_009.jpg');
INSERT INTO Products VALUES(10,'Кеды Canvas Woman',1,6,'Классические кеды из ткани','Текстиль, резиновая подошва',5490.0,'IMG_010.jpg');
INSERT INTO Products VALUES(11,'Ботинки Oxford Classic',2,3,'Классические оксфорды со шнуровкой','Натуральная кожа, кожаная подкладка',15990.0,'IMG_011.jpg');
INSERT INTO Products VALUES(12,'Ботинки Chelsea Man',2,2,'Челси на каждый день','Натуральная кожа, подошва ТЭП',12490.0,'IMG_012.jpg');
INSERT INTO Products VALUES(13,'Кроссовки Urban Walk',2,7,'Повседневные кроссовки с мягкой стелькой','Текстиль, амортизирующая стелька',7990.0,'IMG_013.jpg');
INSERT INTO Products VALUES(14,'Туфли Derby',2,1,'Дерби с открытой шнуровкой','Натуральная кожа',13490.0,'IMG_014.jpg');
INSERT INTO Products VALUES(15,'Ботинки зимние Arctic',2,4,'Зимние ботинки для сильных морозов','Кожа, натуральный мех, подошва резина',17990.0,'IMG_015.jpg');
INSERT INTO Products VALUES(16,'Мокасины Drive',2,3,'Мокасины для вождения','Кожа, подошва резина',10990.0,'IMG_016.jpg');
INSERT INTO Products VALUES(17,'Сандалии Trek Sandal',2,2,'Закрытые сандалии для походов','Кожа, текстиль',6490.0,'IMG_017.jpg');
INSERT INTO Products VALUES(18,'Кеды Classic Low',2,6,'Низкие кеды','Текстиль',4990.0,'IMG_018.jpg');
INSERT INTO Products VALUES(19,'Ботинки Work Pro',2,5,'Рабочие ботинки с защитным подноском','Кожа, стальной подносок',9990.0,'IMG_019.jpg');
INSERT INTO Products VALUES(20,'Ботинки Kids Winter',3,8,'Зимние ботинки для детей','Мембрана, искусственный мех',5990.0,'IMG_020.jpg');
INSERT INTO Products VALUES(21,'Кроссовки Kids Run',3,9,'Лёгкие кроссовки для прогулок и спорта','Сетка, синтетика',4990.0,'IMG_021.jpg');
INSERT INTO Products VALUES(22,'Сандалии Kids Summer',3,8,'Летние сандалии на липучке','Искусственная кожа',2990.0,'IMG_022.jpg');
INSERT INTO Products VALUES(23,'Сапоги резиновые Rain',3,10,'Резиновые сапоги для дождя','Резина, текстильная подкладка',2490.0,'IMG_023.jpg');
INSERT INTO Products VALUES(24,'Ботинки School',3,3,'Школьные ботинки','Натуральная кожа',6990.0,'IMG_024.jpg');
INSERT INTO Products VALUES(25,'Кеды Kids Canvas',3,6,'Детские кеды','Текстиль',3490.0,'IMG_025.jpg');
INSERT INTO Products VALUES(26,'Кроссовки Air Max 270',4,11,'Кроссовки с воздушной подушкой Air','Текстиль, синтетика, амортизация Air',13990.0,'IMG_026.jpg');
INSERT INTO Products VALUES(27,'Кроссовки Ultraboost Light',4,9,'Беговые кроссовки с подошвой Boost','Primeknit, подошва Boost',17990.0,'IMG_027.jpg');
INSERT INTO Products VALUES(28,'Кроссовки Run Fast 3',4,12,'Кроссовки для бега','Сетка, пена ProFoam',7490.0,'IMG_028.jpg');
INSERT INTO Products VALUES(29,'Бутсы Predator Club',4,9,'Футбольные бутсы для искусственного газона','Синтетика, шипы ТПУ',6990.0,'IMG_029.jpg');
INSERT INTO Products VALUES(30,'Кроссовки Pegasus 41',4,11,'Универсальные беговые кроссовки','Сетка, пена React',12990.0,'IMG_030.jpg');
INSERT INTO Products VALUES(31,'Кроссовки баскетбольные Court',4,11,'Баскетбольные кроссовки с высоким верхом','Кожа, текстиль',11490.0,'IMG_031.jpg');
INSERT INTO Products VALUES(32,'Кроссовки Trail Master',4,13,'Трейловые кроссовки с мембраной','Мембрана, подошва Contagrip',14490.0,'IMG_032.jpg');
INSERT INTO Products VALUES(33,'Кроссовки Gel Rider',4,14,'Кроссовки с гелевой амортизацией','Сетка, гель',9490.0,'IMG_033.jpg');
CREATE TABLE Stock (
    product_id INTEGER NOT NULL
               REFERENCES Products(id) ON UPDATE CASCADE ON DELETE CASCADE,
    size_id    INTEGER NOT NULL
               REFERENCES Sizes(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity   INTEGER NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    PRIMARY KEY (product_id, size_id)
);
INSERT INTO Stock VALUES(1,9,5);
INSERT INTO Stock VALUES(1,10,4);
INSERT INTO Stock VALUES(1,11,3);
INSERT INTO Stock VALUES(2,9,2);
INSERT INTO Stock VALUES(2,12,3);
INSERT INTO Stock VALUES(2,13,5);
INSERT INTO Stock VALUES(3,10,2);
INSERT INTO Stock VALUES(3,13,1);
INSERT INTO Stock VALUES(4,12,5);
INSERT INTO Stock VALUES(4,13,12);
INSERT INTO Stock VALUES(4,14,6);
INSERT INTO Stock VALUES(5,10,6);
INSERT INTO Stock VALUES(5,11,4);
INSERT INTO Stock VALUES(5,12,5);
INSERT INTO Stock VALUES(6,9,3);
INSERT INTO Stock VALUES(6,12,8);
INSERT INTO Stock VALUES(6,14,8);
INSERT INTO Stock VALUES(7,9,10);
INSERT INTO Stock VALUES(7,12,3);
INSERT INTO Stock VALUES(7,14,15);
INSERT INTO Stock VALUES(8,11,1);
INSERT INTO Stock VALUES(8,13,2);
INSERT INTO Stock VALUES(9,9,5);
INSERT INTO Stock VALUES(9,13,6);
INSERT INTO Stock VALUES(9,14,3);
INSERT INTO Stock VALUES(10,9,12);
INSERT INTO Stock VALUES(10,11,8);
INSERT INTO Stock VALUES(10,12,4);
INSERT INTO Stock VALUES(11,14,3);
INSERT INTO Stock VALUES(11,15,4);
INSERT INTO Stock VALUES(11,19,15);
INSERT INTO Stock VALUES(12,14,6);
INSERT INTO Stock VALUES(12,16,15);
INSERT INTO Stock VALUES(12,18,5);
INSERT INTO Stock VALUES(13,13,2);
INSERT INTO Stock VALUES(13,14,8);
INSERT INTO Stock VALUES(13,19,10);
INSERT INTO Stock VALUES(14,13,1);
INSERT INTO Stock VALUES(14,15,2);
INSERT INTO Stock VALUES(15,14,10);
INSERT INTO Stock VALUES(15,16,12);
INSERT INTO Stock VALUES(15,18,4);
INSERT INTO Stock VALUES(16,14,15);
INSERT INTO Stock VALUES(16,17,6);
INSERT INTO Stock VALUES(16,19,10);
INSERT INTO Stock VALUES(17,14,3);
INSERT INTO Stock VALUES(17,15,2);
INSERT INTO Stock VALUES(17,16,3);
INSERT INTO Stock VALUES(17,18,4);
INSERT INTO Stock VALUES(18,16,3);
INSERT INTO Stock VALUES(18,18,10);
INSERT INTO Stock VALUES(18,19,10);
INSERT INTO Stock VALUES(19,13,3);
INSERT INTO Stock VALUES(19,15,15);
INSERT INTO Stock VALUES(19,17,6);
INSERT INTO Stock VALUES(19,19,8);
INSERT INTO Stock VALUES(20,2,12);
INSERT INTO Stock VALUES(20,4,2);
INSERT INTO Stock VALUES(20,5,6);
INSERT INTO Stock VALUES(21,2,6);
INSERT INTO Stock VALUES(21,6,15);
INSERT INTO Stock VALUES(21,7,5);
INSERT INTO Stock VALUES(22,3,1);
INSERT INTO Stock VALUES(22,8,2);
INSERT INTO Stock VALUES(23,1,3);
INSERT INTO Stock VALUES(23,4,8);
INSERT INTO Stock VALUES(23,6,6);
INSERT INTO Stock VALUES(24,1,3);
INSERT INTO Stock VALUES(24,2,3);
INSERT INTO Stock VALUES(24,5,12);
INSERT INTO Stock VALUES(25,2,12);
INSERT INTO Stock VALUES(25,3,15);
INSERT INTO Stock VALUES(25,6,4);
INSERT INTO Stock VALUES(26,15,5);
INSERT INTO Stock VALUES(26,17,15);
INSERT INTO Stock VALUES(26,18,5);
INSERT INTO Stock VALUES(27,14,15);
INSERT INTO Stock VALUES(27,15,12);
INSERT INTO Stock VALUES(27,16,3);
INSERT INTO Stock VALUES(28,10,2);
INSERT INTO Stock VALUES(28,12,15);
INSERT INTO Stock VALUES(28,14,5);
INSERT INTO Stock VALUES(29,12,1);
INSERT INTO Stock VALUES(29,18,1);
INSERT INTO Stock VALUES(30,9,8);
INSERT INTO Stock VALUES(30,10,3);
INSERT INTO Stock VALUES(30,12,15);
INSERT INTO Stock VALUES(31,12,15);
INSERT INTO Stock VALUES(31,13,4);
INSERT INTO Stock VALUES(31,16,12);
INSERT INTO Stock VALUES(32,12,3);
INSERT INTO Stock VALUES(32,15,3);
INSERT INTO Stock VALUES(32,16,10);
INSERT INTO Stock VALUES(33,15,2);
INSERT INTO Stock VALUES(33,16,3);
INSERT INTO Stock VALUES(33,19,2);
CREATE TABLE Orders (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    external_number INTEGER UNIQUE,
    order_date      TEXT NOT NULL,                       -- дата в виде ГГГГ-ММ-ДД
    client_id       INTEGER NOT NULL
                    REFERENCES Users(id) ON UPDATE CASCADE ON DELETE RESTRICT
);
INSERT INTO Orders VALUES(1,1001,'2026-09-24',11);
INSERT INTO Orders VALUES(2,1002,'2026-09-17',12);
INSERT INTO Orders VALUES(3,1003,'2026-09-12',4);
INSERT INTO Orders VALUES(4,1004,'2026-09-08',7);
INSERT INTO Orders VALUES(5,1005,'2026-09-03',10);
INSERT INTO Orders VALUES(6,1006,'2026-07-20',4);
INSERT INTO Orders VALUES(7,1007,'2026-07-14',7);
INSERT INTO Orders VALUES(8,1008,'2026-07-05',10);
INSERT INTO Orders VALUES(9,1009,'2026-06-22',4);
INSERT INTO Orders VALUES(10,1010,'2026-06-09',7);
CREATE TABLE OrderItems (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL
               REFERENCES Orders(id) ON UPDATE CASCADE ON DELETE CASCADE,
    product_id INTEGER NOT NULL
               REFERENCES Products(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    size_id    INTEGER NOT NULL
               REFERENCES Sizes(id) ON UPDATE CASCADE ON DELETE RESTRICT,
    quantity   INTEGER NOT NULL CHECK (quantity > 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0)
);
INSERT INTO OrderItems VALUES(1,1,18,19,1,4990.0);
INSERT INTO OrderItems VALUES(2,1,33,15,1,9490.0);
INSERT INTO OrderItems VALUES(3,1,16,17,1,10990.0);
INSERT INTO OrderItems VALUES(4,2,9,14,1,4990.0);
INSERT INTO OrderItems VALUES(5,2,24,2,2,6990.0);
INSERT INTO OrderItems VALUES(6,2,20,4,1,5990.0);
INSERT INTO OrderItems VALUES(7,3,13,14,2,7990.0);
INSERT INTO OrderItems VALUES(8,3,21,2,1,4990.0);
INSERT INTO OrderItems VALUES(9,3,12,14,1,12490.0);
INSERT INTO OrderItems VALUES(10,3,4,13,1,14990.0);
INSERT INTO OrderItems VALUES(11,4,5,10,1,9490.0);
INSERT INTO OrderItems VALUES(12,4,11,19,2,15990.0);
INSERT INTO OrderItems VALUES(13,5,22,3,2,2990.0);
INSERT INTO OrderItems VALUES(14,5,21,7,1,4990.0);
INSERT INTO OrderItems VALUES(15,5,10,12,1,5490.0);
INSERT INTO OrderItems VALUES(16,6,17,18,1,6170.0);
INSERT INTO OrderItems VALUES(17,6,1,9,2,8540.0);
INSERT INTO OrderItems VALUES(18,6,18,16,1,4740.0);
INSERT INTO OrderItems VALUES(19,7,19,17,2,9490.0);
INSERT INTO OrderItems VALUES(20,7,31,16,1,10920.0);
INSERT INTO OrderItems VALUES(21,7,33,15,1,9020.0);
INSERT INTO OrderItems VALUES(22,8,14,13,1,12820.0);
INSERT INTO OrderItems VALUES(23,8,10,12,1,5220.0);
INSERT INTO OrderItems VALUES(24,8,3,13,1,7120.0);
INSERT INTO OrderItems VALUES(25,9,3,10,1,7120.0);
INSERT INTO OrderItems VALUES(26,9,26,17,1,13290.0);
INSERT INTO OrderItems VALUES(27,9,21,7,1,4740.0);
INSERT INTO OrderItems VALUES(28,10,9,13,1,4740.0);
INSERT INTO OrderItems VALUES(29,10,4,12,1,14240.0);
INSERT INTO OrderItems VALUES(30,10,27,14,2,17090.0);
INSERT INTO sqlite_sequence VALUES('Sizes',19);
INSERT INTO sqlite_sequence VALUES('Roles',3);
INSERT INTO sqlite_sequence VALUES('Users',12);
INSERT INTO sqlite_sequence VALUES('Categories',4);
INSERT INTO sqlite_sequence VALUES('Manufacturers',14);
INSERT INTO sqlite_sequence VALUES('Products',33);
INSERT INTO sqlite_sequence VALUES('Orders',10);
INSERT INTO sqlite_sequence VALUES('OrderItems',30);
CREATE INDEX idx_users_role          ON Users(role_id);
CREATE INDEX idx_products_category   ON Products(category_id);
CREATE INDEX idx_products_manuf      ON Products(manufacturer_id);
CREATE INDEX idx_products_name       ON Products(name);
CREATE INDEX idx_stock_size          ON Stock(size_id);
CREATE INDEX idx_orders_date         ON Orders(order_date);
CREATE INDEX idx_orders_client       ON Orders(client_id);
CREATE INDEX idx_orderitems_order    ON OrderItems(order_id);
CREATE INDEX idx_orderitems_product  ON OrderItems(product_id);
COMMIT;
