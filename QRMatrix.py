import PIL, numpy, sys, operator
from PIL import Image


class QRMatrix:
    """
    The QRMatrix Class that will allow users to encode and decode QR Codes.
    """

    def __init__(self, image="", message=""):
        """
        Creates a QRMatrix object. Only one parameter (image or message) can bbe filled. It's from that
        where this code will decide whether to encode or decode. If an image path is insterted, it will
        decode the image. Otherwise it will encode.

        When decoding, it begins by using numpy to convert the image in binary ndary array. 0 will refer
        to black pixels and 255 will refer to white pixels. Afterwards, it is converted into a list of lists where
        white space is then trimmed and the matrix is then scaled.
        :param image: The path to the image.
        :param message: The message to be encoded.
        :return:
        """
        if not bool(image) ^ bool(message):
            raise Exception("You can only have an image or message. Not both or neither.")
        elif len(image) > 0:
            self.matrix = numpy.asarray(Image.open(image).convert('L')).tolist()
            self.__trimWhiteSpace()
            self.__scaleMatrix()  # May need to modify later if using real images.
        else:
            print("Matrix Maker has not been implemented yet")

    def __str__(self):
        """
        Creates an n x n matrix representation of the QRMatrix object. For this representation, 255 will become 1.
        :return: The String representation of a QRMatrix.
        """
        for row in self.matrix:
            print [i if i != 255 else 1 for i in row]
        return ""

    def decode(self):
        """
        Decodes the matrix.

        :return:
        """
        demasked_matrix = self.demask()
        self.version = ((len(self.matrix) - 21) / 4) + 1
        self.representation = self.decodeBits(demasked_matrix, len(self.matrix) - 2, len(self.matrix) - 2, 0)
        self.length = self.decodeBits(demasked_matrix, len(self.matrix) - 6, len(self.matrix) - 2, 0)
        word = ""

        xDisplacement, yDisplacement = len(self.matrix) -6, len(self.matrix)-2
        orientation = 0
        for i in range(self.length + 1):
            word+=chr(self.decodeBits(demasked_matrix,  xDisplacement, yDisplacement, orientation))
            if self.needs_to_rotate(xDisplacement, yDisplacement, orientation):
                orientation+=1
                count=0
            if orientation > 3:
                orientation = 0
            xDisplacement, yDisplacement = self.get_next_coordinates(orientation, xDisplacement, yDisplacement)

        return word

    def needs_to_rotate(self, x, y, current_orientation):
        """

        :param current_oreintation:
        :param blocks_evaluated_since_last_switch:
        :return:
        """
        if (current_orientation == 1 or current_orientation == 3):
            return True
        else:
            return self.out_of_bounds(x,y,current_orientation)

    def out_of_bounds(self, x ,y, current_orientation):
        x_new, y_new = self.get_next_coordinates(current_orientation, x, y)
        if x_new > len(self.matrix) - 1 or y_new > len(self.matrix) - 1:
            return True
        elif x_new < 0 or y_new < 0:
            return True
        elif x_new <=9 and (y_new <= 9 or y_new >= len(self.matrix) - 8):
            return True
        elif x_new <=9 and y_new >= len(self.matrix) - 8:
            return True
        else:
            return False

    def get_next_coordinates(self, orientation, x, y):
        """

        :param orientation:
        :return:
        """

        if (orientation == 0):
            return (x-4, y)
        elif (orientation == 1):
            return  (x-1, y-2)
        elif (orientation == 2):
            return (x+4, y)
        else:
            return (x+1, y-2)

    def sum_quad_binary(self, demasked_matrix, x_cor_func, y_cor_func, start_row, start_column, power=1):
        """

        :param x_cor_func:
        :param y_cor_func:
        :return:
        """
        x, y, total = 0, 0, 0
        while x < 2:
            y = 0
            while y < 2:
                try:
                    total += demasked_matrix[x_cor_func(start_row, x)][y_cor_func(start_column, y)] * power
                except IndexError:
                    y += 1
                    continue
                power <<= 1
                y += 1
            x += 1
        return total

    def decodeBits(self, demasked_matrix, start_row, start_column, orientation):
        """
        Gotta start on -1 length is greater than index by one.
        :param demasked_matrix: The demasked matrix.
        :param start_row: The starting row.
        :param start_column: The starting columns.
        :param orientation: The direction of the value. 0 means going up, 1 means going left, 2 means going down.
        :return: The ASCII value.
        """

        if orientation == 0:
            total = self.sum_quad_binary(demasked_matrix, operator.add, operator.add, start_row, start_column, power=1)
            total += self.sum_quad_binary(demasked_matrix, operator.add, operator.add, start_row + 2, start_column, power=16)
        elif orientation == 1:
            total = self.sum_quad_binary(demasked_matrix, operator.sub, operator.add, start_row, start_column, power=1)
            total += self.sum_quad_binary(demasked_matrix, operator.add, operator.add, start_row - 1, start_column + 2,
                                        power=16)
        elif orientation == 2:
            total = self.sum_quad_binary(demasked_matrix, operator.sub, operator.add, start_row, start_column, power=1)
            total += self.sum_quad_binary(demasked_matrix, operator.sub, operator.add, start_row - 2, start_column,
                                        power=16)
        elif orientation == 3:
            total = self.sum_quad_binary(demasked_matrix, operator.add, operator.add, start_row, start_column, power=1)
            total += self.sum_quad_binary(demasked_matrix, operator.sub, operator.add, start_row+1, start_column + 2,
                                        power=16)
        else:
            raise Exception("Improper orientation value.")
        return total

    def demask(self):
        """
        Removes the mask on the QR Matrix. This creates a matrix that has 1 represent black spots and 0 represent
        white spots, the oppisite of the normal matrix. Also accounts for skipped row and column.

        :return: The unmasked QR Code
        """
        mask = self.extractMaskPattern()
        decodedMatrix = []
        y = 0
        while y < len(self.matrix):
            row = []
            x = 0
            while x < len(self.matrix[0]):
                modifyValue = self.matrix[y][x]
                if (modifyValue == 255):
                    modifyValue = 1
                row += [(~modifyValue + 2 ^ ~mask[y][x] + 2)]
                x += 1
            decodedMatrix += [row]
            y += 1
        return decodedMatrix

    def encode(self):
        """
        Encodes the matrix.
        :return:
        """

        return

    def extractMaskPattern(self):
        """
        Find the mask pattern in the QR Code and returns the bit array representation of it. Remember that 255 is used
        to represent white and 0 is used to represet black. These 3 bits will correspond with a power of 2 to create
        a unique value. This will then be used to create a mask patter to decode things. Remember that row and column
        7 must be skipped because they are special. Last part needed to adjust for shift.

        :return: The mask pattern created.
        """

        maskPattern = self.matrix[8][2:5]
        power = 1
        total = 0
        for i in maskPattern:
            if i == 0:
                total += power
            power <<= 1

        maskMatrix = []
        j = 0
        for row in self.matrix:
            i = 0
            newRow = []
            for val in self.matrix[j]:
                if self.extractMaskNumberBoolean(total, i, j):
                    newRow += [0]
                else:
                    newRow += [1]
                i += 1
            j += 1
            maskMatrix += [newRow]
        return maskMatrix

    def extractMaskNumberBoolean(self, number, j, i):
        """
        The forumlas were copied inversely so the operands have been reversed in this function. This function
        returns a boolean that matches a certain pattern

        :param number: The mask pattern number.
        :param i: The x position.
        :param j: The y position.
        :return: The boolean of whether or not a spot should be inverted.
        """
        if number == 1:
            return i % 2 == 0
        elif number == 2:
            return ((i * j) % 3 + i + j) % 2 == 0
        elif number == 3:
            return (i + j) % 3 == 0
        elif number == 4:
            return (i / 2 + j / 3) % 2 == 0
        elif number == 5:
            return (i + j) % 2 == 0
        elif number == 6:
            return ((i * j) % 3 + i * j) % 2 == 0
        elif number == 7:
            return j % 3 == 0

    def __trimWhiteSpace(self):
        """
        Removes every row that only contains white space. Once row with without white space is discovered,
        find the starting location of the black pixel and the last location of the black pixel. Use these variables
        to trim of remaining white space througout the image.

        :return: The matrix without trailing white pixels.
        """

        isUsefulRow = False
        trimmedMatrix = []
        startPoint, endPoint = 0, 0
        for row in self.matrix:
            if isUsefulRow:
                if len(trimmedMatrix) == endPoint - startPoint:
                    break
                trimmedMatrix += [row[startPoint: endPoint]]
            elif not self.__rowIsWhiteSpace(row):
                isUsefulRow = True
                startPoint, endPoint = self.__extractEndPoints(row)
        self.matrix = trimmedMatrix

    def __extractEndPoints(self, firstRow):
        """
        Extracts the dimensions of the matrix by utilizing the first row. This finds the first black spot and the last.

        :param firstRow: The first row with data.
        :return: A tuple of index of the first useful bit and the last useful bit.
        """
        wastedSpace = 0
        for num in firstRow:
            if num == 255:
                wastedSpace += 1
            else:
                break
        lastBlackIndex, count = wastedSpace, wastedSpace
        for num in firstRow[wastedSpace:]:
            if num == 0:
                lastBlackIndex = count
            count += 1
        return (wastedSpace, lastBlackIndex)

    def __rowIsWhiteSpace(self, row):
        """
        Returns a boolean of whether row is white space.

        :param row: A row of a matrix.
        :return: True if all white pixels, false otherwise.
        """
        for i in row:
            if i != 255:
                return False
        return True

    def __findRatio(self, matrix):
        """
        Finds and returns the ratio of the image to it's 1 pixel per black pixel equivalent.

        :return: The scale of the matrix
        """
        # TODO: Use Finder Pattern Method

        for row in matrix:
            scale = 0
            for num in row:
                scale += 1
                if num == 255:
                    return scale // 7
        raise Exception("This image is not binary!")

    def __scaleMatrix(self):
        """
        Scales the matrix to the smallest size possible

        :return: Nothing
        """
        ratio = self.__findRatio(self.matrix)
        scaledMatrix = []
        yCount = 0
        for row in self.matrix:
            if yCount % ratio == 0:
                xCount = 0
                newRow = []
                for value in row:
                    if xCount % ratio == 0:
                        newRow += [value]
                    xCount += 1
                scaledMatrix += [newRow]
            yCount += 1
        self.matrix = scaledMatrix

    def __find_usable_space(self):
        """

        :return:
        """
        return len(self.matrix) - 7 - 2

if __name__ == "__main__":
    if str(sys.argv[1]) == "decode" or sys.argv[1] == "encode":
        QRCode = QRMatrix(sys.argv[2])
        print(QRCode.decode())
        print(len(QRCode.matrix))

