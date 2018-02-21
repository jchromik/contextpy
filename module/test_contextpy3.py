import unittest

from contextpy3 import (
    Layer, proceed, active_layer, active_layers, inactive_layer,
    inactive_layers, after, around, before, base, global_activate_layer,
    global_deactivate_layer)

whoLayer = Layer("WhoLayer")
detailsLayer = Layer("DetailsLayer")
yearLayer = Layer("YearLayer")

class Greeting(object):

    def __init__(self, greets, who, fromPlace, year):
        self.greets = greets
        self.who = who
        self.fromPlace = fromPlace
        self.year = year
       
    def __str__(self):
        return self.greets
    
    @around(whoLayer)
    def __str__(self):
        return " ".join((proceed(), self.who))
    
    @after(detailsLayer)
    def __str__(self,  *args, **kwargs):
        return " ".join((kwargs["__result__"], "from", self.fromPlace, "in", str(self.year)))
              
    @around(detailsLayer)
    def setYear(self, value):
        self.year = 500

    @base
    def setYear(self, value):
        self.year = value    
        
    @around(yearLayer)
    def setYear(self, value):
        pass

    @before(yearLayer)
    def setYear(self, value):
        self.year = value + 1 
            
    @after(yearLayer)
    def setYear(self, value, *args, **kwargs):
        self.year = self.year + 1

class GermanGreeting(Greeting):

    @around(detailsLayer)
    def __str__(self):
        return " ".join(("German:",  super(GermanGreeting, self).__str__()))
    
    @around(whoLayer)
    def __str__(self):
        return " ".join((proceed(), "Aus:", self.who))

    @base
    def __str__(self):
        return super(GermanGreeting, self).__str__()

def hallo(self, str):
    return str

@around(detailsLayer)
def hallo(self, str):
    return " ".join(("Deutsch:", proceed(str)))


class Address(object):
    attribute = ""

    def __init__(self, city, street, zip):
        self.city = city
        self.street = street
        self.zip = zip

    def __str__(self):
        return self.city

    @around(detailsLayer)
    def __str__(self):
        return " ".join((self.street, proceed(), str(self.zip)))

    def classAddress(cls, str):
        return "Address: " + str

    classAddress = classmethod(classAddress)
    
    @around(detailsLayer)
    @classmethod
    def classAddress(cls, str):
        return proceed(str + " More Details")
    
    @before(whoLayer)
    @classmethod
    def classAddress(cls, str):
        cls.attribute = "Class Method"
        
    @after(whoLayer)
    @classmethod
    def classAddress(cls, str, __result__):
        result = " ".join((cls.attribute, __result__, "After"))
        cls.attribute = ""
        return result
    
    @staticmethod
    def staticAddress(str):
        return "Address: " + str
    
    @around(detailsLayer)
    @staticmethod
    def staticAddress(str):
        return proceed(str + " More Details")
           
    @after(whoLayer)
    @staticmethod
    def staticAddress(str, __result__):
        result = " ".join((__result__, "After"))
        return result

class Nonsense(object):
    @around(whoLayer)
    def just_call_proceed(self):
        proceed()

# At the first element of all partial methods, @base is not necessary
@base
def answerFunction(string):
    return string

@around(whoLayer)
def answerFunction(string):
    return " ".join(("answerFunction:", proceed(string)))

@around(detailsLayer)
def answerFunction(string):
    return " ".join((proceed(string), "(Normal Python Module Function)"))

class TestContextPy(unittest.TestCase):
    
    def setUp(self):
        self.greeting = Greeting("Hello", "World", "Potsdam", 2008)
        self.address = Address("Potsdam", "Saarmunder Str. 9", 14478)
    
    def tearDown(self):
        pass

    def testWithoutLayer(self):
        self.assertEqual(self.greeting.__str__(), "Hello")
        self.assertEqual(self.greeting.year, 2008)
        self.greeting.setYear(1999)
        self.assertEqual(self.greeting.year, 1999)

    def testWithSingleLayer(self):
        self.assertEqual(self.greeting.__str__(), "Hello")
        with active_layer(whoLayer):
            self.assertEqual(self.greeting.__str__(), "Hello World")
        self.assertEqual(self.greeting.__str__(), "Hello")
        
    def testWithDoubleLayer(self):
        self.assertEqual(self.greeting.__str__(), "Hello")
        with active_layer(detailsLayer):
            self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008")
            with active_layer(whoLayer):
                self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008 World")
                with inactive_layer(whoLayer):
                    self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008")
            self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008")
        with active_layers(detailsLayer, whoLayer):
            self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008 World")
        with active_layers(whoLayer, detailsLayer):
            self.assertEqual(self.greeting.__str__(), "Hello World from Potsdam in 2008")
        self.assertEqual(self.greeting.__str__(), "Hello")
    
    def testMultipleActivation(self):
        self.assertEqual(self.greeting.__str__(), "Hello")
        with active_layer(detailsLayer):
            self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008")
            with active_layer(detailsLayer):
                self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008")
                with active_layer(whoLayer):
                    self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008 World")
    
    def testGlobalActivation(self):
        self.assertEqual(self.greeting.__str__(), "Hello")
        global_activate_layer(whoLayer)
        self.assertEqual(self.greeting.__str__(), "Hello World")
        global_activate_layer(detailsLayer)
        self.assertEqual(self.greeting.__str__(), "Hello World from Potsdam in 2008")
        global_deactivate_layer(whoLayer)
        self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008")
        global_deactivate_layer(detailsLayer)
        self.assertEqual(self.greeting.__str__(), "Hello")
        
        # Test Exception Handling
        global_activate_layer(whoLayer)
        self.assertRaises(ValueError, global_activate_layer, whoLayer)
        global_deactivate_layer(whoLayer)
        self.assertRaises(ValueError, global_deactivate_layer, whoLayer)
        
    def testYearLayer(self):
        self.assertEqual(self.greeting.year, 2008)
        self.greeting.setYear(1999)
        self.assertEqual(self.greeting.year, 1999)
        with active_layer(yearLayer):
            self.greeting.setYear(1998)    
        self.assertEqual(self.greeting.year, 2000)
        self.greeting.setYear(1998)
        self.assertEqual(self.greeting.year, 1998)            

    def testCrossCutLayer(self):
        self.assertEqual(self.greeting.__str__(), "Hello")
        with active_layer(detailsLayer):
            self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008")
            self.greeting.setYear(1999)
            self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 500")
        self.assertEqual(self.greeting.year, 500)
        self.assertEqual(self.address.__str__(), "Potsdam")
        self.greeting.setYear(2008)
        self.assertEqual(self.address.__str__(), "Potsdam")                
        with active_layer(detailsLayer):
            self.assertEqual(self.greeting.__str__(), "Hello from Potsdam in 2008")
            self.assertEqual(self.address.__str__(), "Saarmunder Str. 9 Potsdam 14478")
    
    def testClassMethods(self):
        self.assertEqual(Address("city", "street", 123).classAddress("Test Address"), "Address: Test Address")
        self.assertEqual(Address.classAddress("Test Address"), "Address: Test Address")
        with active_layer(detailsLayer):
            self.assertEqual(Address.classAddress("Test Address"), "Address: Test Address More Details")
        with active_layer(whoLayer):
            self.assertEqual(Address("city", "street", 123).classAddress("Test Address"), "Class Method Address: Test Address After")
            with active_layer(detailsLayer):
                self.assertEqual(Address.classAddress("Test Address"), "Class Method Address: Test Address More Details After")

    def testStaticMethods(self):
        self.assertEqual(Address.staticAddress("Test Address"), "Address: Test Address")
        self.assertEqual(Address("city", "street", 123).staticAddress("Test Address"), "Address: Test Address")
        with active_layer(detailsLayer):
            self.assertEqual(Address.staticAddress("Test Address"), "Address: Test Address More Details")
        with active_layer(whoLayer):
            self.assertEqual(Address.staticAddress("Test Address"), "Address: Test Address After")
            with active_layer(detailsLayer):
                self.assertEqual(Address("city", "street", 123).staticAddress("Test Address"), "Address: Test Address More Details After")
    
    def testFunctions(self):
        self.assertEqual(answerFunction("Hello World"), "Hello World")
        with active_layer(whoLayer):
            self.assertEqual(answerFunction("Hello World"), "answerFunction: Hello World")
        with active_layer(detailsLayer):
            self.assertEqual(answerFunction("Hello World"), "Hello World (Normal Python Module Function)")
            with active_layer(whoLayer):
                self.assertEqual(answerFunction("Hello World"), "answerFunction: Hello World (Normal Python Module Function)")
        self.assertEqual(answerFunction("Hello World"), "Hello World")
    
    def testInheritance(self):
        greetings = GermanGreeting("Hallo", "Welt", "Potsdam", 2008)
        self.assertEqual(greetings.__str__(), "Hallo")
        with active_layer(whoLayer):
            self.assertEqual(greetings.__str__(), "Hallo Welt Aus: Welt")
        with active_layer(detailsLayer):
            self.assertEqual(greetings.__str__(), "German: Hallo from Potsdam in 2008")
            with active_layer(whoLayer):
                self.assertEqual(greetings.__str__(), "German: Hallo from Potsdam in 2008 Welt Aus: Welt")
        
    def testLateMethodBinding(self):
        germanGreet = GermanGreeting("Hallo", "Welt", "Potsdam", 2008)
        self.assertRaises(AttributeError, getattr, germanGreet, "hallo")
        GermanGreeting.hallo = hallo
        self.assertEqual(germanGreet.hallo("Hallo"), "Hallo")
        with active_layer(detailsLayer):
            self.assertEqual(germanGreet.hallo("Hallo"), "Deutsch: Hallo")

    def testStringRepresentations(self):
        self.assertEqual(whoLayer.__str__(), "<layer WhoLayer>")
        self.assertEqual(detailsLayer.__str__(), "<layer DetailsLayer>")
        self.assertEqual(yearLayer.__str__(), "<layer YearLayer>")
        self.assertEqual(whoLayer.__repr__(), "layer(name=\"WhoLayer\")")
        self.assertEqual(detailsLayer.__repr__(), "layer(name=\"DetailsLayer\")")
        self.assertEqual(yearLayer.__repr__(), "layer(name=\"YearLayer\")")

    def testInactive_layers(self):
        with active_layers(whoLayer, detailsLayer, yearLayer):
            with inactive_layers(detailsLayer, yearLayer):
                self.assertEqual(self.greeting.__str__(), "Hello World")

    def testProceedInInnermostThrowsException(self):
        nonsense = Nonsense()
        with active_layer(whoLayer):
            self.assertRaises(Exception, nonsense.just_call_proceed)

    def testLayerMerging(self):
        global_activate_layer(whoLayer)
        global_activate_layer(detailsLayer)
        with active_layer(detailsLayer):
            self.assertEqual(answerFunction("Hello World"),
                             "answerFunction: Hello World (Normal Python Module Function)")
        global_deactivate_layer(whoLayer)
        global_deactivate_layer(detailsLayer)

if __name__ == '__main__':
    unittest.main()